// src/utils/api.js
// Production-grade API client architecture for BluCare+ with retry strategy,
// exponential backoff, Clerk JWT injection, offline detection, & SSE streaming.
import { getAuthorizedHeaders } from './auth';
import { logger } from './logger';

const DEFAULT_BASE_URL = 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 45000;
const MAX_RETRIES = 2;

export class ApiError extends Error {
  constructor(message, status = 500, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export function getApiBaseUrl() {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && envUrl.trim() !== '') {
    return envUrl.replace(/\/+$/, '');
  }
  return DEFAULT_BASE_URL;
}

/**
 * Executes an HTTP request with exponential backoff retries for transient failures.
 */
export async function request(endpoint, options = {}) {
  const {
    method = 'GET',
    body = null,
    headers = {},
    getToken = null,
    timeout = DEFAULT_TIMEOUT_MS,
    signal = null,
    retries = MAX_RETRIES,
  } = options;

  // Offline detection check
  if (typeof navigator !== 'undefined' && !navigator.onLine) {
    throw new ApiError('No internet connection. Please check your network and try again.', 0);
  }

  // Ensure /api/v1 prefix unless calling root system health endpoints
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const path = cleanEndpoint.startsWith('/api/v1') || cleanEndpoint.startsWith('/health')
    ? cleanEndpoint
    : `/api/v1${cleanEndpoint}`;
  const url = `${getApiBaseUrl()}${path}`;

  let attempt = 0;
  let lastError = null;

  while (attempt <= retries) {
    attempt++;

    // 1. Generate authorized headers via Clerk auth helper
    const authHeaders = await getAuthorizedHeaders(getToken);
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

    const finalHeaders = {
      ...authHeaders,
      ...headers,
    };
    if (isFormData) {
      delete finalHeaders['Content-Type']; // Let browser set boundary
    }

    // 2. Setup timeout AbortController
    const timeoutController = new AbortController();
    const timeoutId = setTimeout(() => {
      timeoutController.abort(new Error(`Request timeout after ${timeout}ms`));
    }, timeout);

    if (signal) {
      if (signal.aborted) {
        clearTimeout(timeoutId);
        throw new ApiError('Request cancelled', 0);
      }
      signal.addEventListener('abort', () => timeoutController.abort(signal.reason));
    }

    try {
      const response = await fetch(url, {
        method,
        headers: finalHeaders,
        body: body ? (isFormData ? body : typeof body === 'string' ? body : JSON.stringify(body)) : null,
        signal: timeoutController.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorDetail = null;
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

        try {
          const errorJson = await response.json();
          errorDetail = errorJson.detail || errorJson;
          if (typeof errorJson.detail === 'string') {
            errorMessage = errorJson.detail;
          } else if (Array.isArray(errorJson.detail)) {
            errorMessage = errorJson.detail.map((e) => e.msg || e).join('; ');
          }
        } catch {
          // Non-JSON response
        }

        const isTransient = [502, 503, 504].includes(response.status);
        if (isTransient && attempt <= retries) {
          const delay = Math.pow(2, attempt - 1) * 1000;
          logger.warn(`Transient HTTP ${response.status} on ${endpoint}. Retrying in ${delay}ms...`);
          await new Promise((r) => setTimeout(r, delay));
          continue;
        }

        throw new ApiError(errorMessage, response.status, errorDetail);
      }

      if (response.status === 204) return null;
      return await response.json();
    } catch (err) {
      clearTimeout(timeoutId);

      if (err instanceof ApiError) {
        throw err;
      }

      if (err.name === 'AbortError') {
        const isTimeout = timeoutController.signal.aborted && (!signal || !signal.aborted);
        const msg = isTimeout ? `Request timed out after ${timeout / 1000}s` : 'Request was cancelled';
        throw new ApiError(msg, 408);
      }

      lastError = err;
      if (attempt <= retries) {
        const delay = Math.pow(2, attempt - 1) * 1000;
        logger.warn(`Network error on ${endpoint}. Retrying attempt ${attempt}/${retries} in ${delay}ms...`);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }

      logger.error(`API Request failed for [${method} ${endpoint}]:`, err);
      throw new ApiError(err.message || 'Network communication failure', 0);
    }
  }

  throw new ApiError(lastError?.message || 'Request failed after retries', 0);
}

/**
 * Domain Modules
 */

export const chatApi = {
  startSession: (initialMessage = null, options = {}) =>
    request('/session/start', {
      method: 'POST',
      body: { initial_message: initialMessage || null },
      ...options,
    }),

  sendMessage: (threadId, message, options = {}) =>
    request('/session/message', {
      method: 'POST',
      body: { thread_id: threadId, message },
      ...options,
    }),

  executeAction: (threadId, actionId, conditionId, coords = {}, options = {}) =>
    request('/session/action', {
      method: 'POST',
      body: {
        thread_id: threadId,
        action_id: actionId,
        condition_id: conditionId,
        latitude: coords?.latitude ?? null,
        longitude: coords?.longitude ?? null,
      },
      ...options,
    }),

  listSessions: (options = {}) =>
    request('/session/list', { method: 'GET', ...options }),

  getSessionHistory: (threadId, options = {}) =>
    request(`/session/${threadId}/history`, { method: 'GET', ...options }),

  deleteSession: (threadId, options = {}) =>
    request(`/session/${threadId}`, { method: 'DELETE', ...options }),

  /**
   * SSE Stream Reader for token-by-token rendering
   */
  streamMessage: async (threadId, message, onChunk, options = {}) => {
    const { getToken, signal } = options;
    const authHeaders = await getAuthorizedHeaders(getToken);
    const url = `${getApiBaseUrl()}/api/v1/session/message/stream`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        ...authHeaders,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ thread_id: threadId, message }),
      signal,
    });

    if (!response.ok) {
      throw new ApiError(`Stream failed with HTTP ${response.status}`, response.status);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;

    while (!done) {
      const { value, done: streamDone } = await reader.read();
      done = streamDone;
      if (value) {
        const text = decoder.decode(value);
        const lines = text.split('\n\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.replace('data: ', '');
            if (data === '[DONE]') break;
            onChunk(data);
          }
        }
      }
    }
  },
};

export const healthApi = {
  checkHealth: (options = {}) => request('/health', { method: 'GET', ...options }),
  checkReadiness: (options = {}) => request('/health/ready', { method: 'GET', ...options }),
};

export const hospitalsApi = {
  getNearbyFacilities: (lat, lng, category = 'all', condition = null, radiusKm = 5, options = {}) => {
    let opts = options;
    let rKm = radiusKm;
    if (typeof radiusKm === 'object' && radiusKm !== null) {
      opts = radiusKm;
      rKm = 5;
    }
    let url = `/hospitals/nearby?lat=${lat}&lng=${lng}&category=${encodeURIComponent(category)}&radius_km=${rKm}`;
    if (condition) {
      url += `&condition=${encodeURIComponent(condition)}`;
    }
    return request(url, { method: 'GET', ...opts });
  },
  getNearbyAmbulances: (lat, lng, options = {}) =>
    request(`/hospitals/nearby?lat=${lat}&lng=${lng}`, { method: 'GET', ...options }),
};

export const userApi = {
  getProfile: (options = {}) => request('/user/profile', { method: 'GET', ...options }),
  updateProfile: (profileData, options = {}) =>
    request('/user/profile', { method: 'PUT', body: profileData, ...options }),
  getSettings: (options = {}) => request('/user/settings', { method: 'GET', ...options }),
  updateSettings: (settingsData, options = {}) =>
    request('/user/settings', { method: 'PUT', body: settingsData, ...options }),
};

export const uploadApi = {
  uploadReport: (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/upload/report', { method: 'POST', body: formData, ...options });
  },
};
