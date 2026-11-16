"""
BluCare+ — Reusable Langfuse Observability Client & Callback Provider.

Provides:
- Singleton Langfuse client lifecycle management.
- Langfuse CallbackHandler creation for LangGraph / LangChain execution.
- HIPAA/GDPR-compliant metadata sanitization (preventing PII/credential leakage).
- Graceful degradation: never throws or disrupts triage operations if Langfuse is disabled or unreachable.
- Non-blocking background event flushing on application shutdown.
"""

import os
import re
import logging
from typing import Optional, Dict, Any, List

from app.core.config import settings

logger = logging.getLogger(__name__)

_langfuse_client = None
_client_initialized = False

# Sensitive keys that should never be sent in Langfuse metadata or tags
SENSITIVE_KEY_PATTERNS = [
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"authorization", re.IGNORECASE),
    re.compile(r"cookie", re.IGNORECASE),
    re.compile(r"bearer", re.IGNORECASE),
    re.compile(r"clerk", re.IGNORECASE),
    re.compile(r"email", re.IGNORECASE),
    re.compile(r"phone", re.IGNORECASE),
    re.compile(r"ssn", re.IGNORECASE),
    re.compile(r"dob", re.IGNORECASE),
    re.compile(r"birth", re.IGNORECASE),
]


def is_langfuse_enabled() -> bool:
    """Returns True if Langfuse is explicitly enabled and API keys are present."""
    if not settings.langfuse_enabled:
        return False
    public_key = settings.langfuse_public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = settings.langfuse_secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    return bool(public_key and secret_key)


def get_langfuse_client():
    """
    Returns the singleton Langfuse client instance if enabled and configured.
    Returns None if Langfuse is disabled or fails initialization.
    """
    global _langfuse_client, _client_initialized
    if _client_initialized:
        return _langfuse_client

    if not is_langfuse_enabled():
        _client_initialized = True
        _langfuse_client = None
        return None

    try:
        public_key = settings.langfuse_public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = settings.langfuse_secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        base_url = settings.langfuse_base_url or os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")

        # Synchronize environment variables for official SDK singletons
        if public_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
        if secret_key:
            os.environ["LANGFUSE_SECRET_KEY"] = secret_key
        if base_url:
            os.environ["LANGFUSE_BASE_URL"] = base_url
            os.environ["LANGFUSE_HOST"] = base_url

        from langfuse import get_client
        client = get_client()
        # Verify credentials without raising
        if client and client.auth_check():
            logger.info("Langfuse observability client successfully initialized and authenticated.")
            _langfuse_client = client
        else:
            logger.warning("Langfuse credentials rejected during auth check. Tracing will be disabled.")
            _langfuse_client = None
    except Exception as e:
        logger.warning("Failed to initialize Langfuse client (%s). Running in degraded mode without tracing.", e)
        _langfuse_client = None

    _client_initialized = True
    return _langfuse_client


def sanitize_trace_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitizes trace metadata to protect medical confidentiality and user identity:
    - Removes secrets, tokens, and credentials.
    - Strips full PII fields (emails, phone numbers, auth headers).
    - Preserves execution metrics, model names, node latencies, and sanitized IDs.
    """
    if not metadata:
        return {}

    sanitized = {}
    for key, value in metadata.items():
        # Check against sensitive patterns
        if any(pattern.search(key) for pattern in SENSITIVE_KEY_PATTERNS):
            continue

        # Nested dict sanitization
        if isinstance(value, dict):
            sanitized[key] = sanitize_trace_metadata(value)
        elif isinstance(value, (str, int, float, bool, list)):
            sanitized[key] = value
        else:
            sanitized[key] = str(value)

    return sanitized


def get_langfuse_callback_handler(
    trace_name: str = "blucare-triage-request",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Creates and returns a Langfuse CallbackHandler for LangChain / LangGraph execution.
    Returns None if Langfuse is disabled or initialization fails.
    """
    if not is_langfuse_enabled():
        return None

    try:
        from langfuse.langchain import CallbackHandler

        public_key = settings.langfuse_public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        # Ensure environment variables are synchronized for SDK
        if public_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
        if settings.langfuse_secret_key:
            os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        if settings.langfuse_base_url:
            os.environ["LANGFUSE_BASE_URL"] = settings.langfuse_base_url

        handler = CallbackHandler(public_key=public_key)

        return handler
    except Exception as e:
        logger.warning("Failed to create Langfuse CallbackHandler (%s). Proceeding without trace.", e)
        return None


def build_langchain_trace_config(
    thread_id: str,
    user_id: str = "anonymous_patient",
    trace_name: str = "blucare-triage-request",
    extra_tags: Optional[List[str]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Builds the LangChain / LangGraph execution config containing callbacks,
    trace metadata, and tags required for full Langfuse observability.
    """
    config: Dict[str, Any] = {
        "configurable": {"thread_id": thread_id},
    }

    if not is_langfuse_enabled():
        return config

    handler = get_langfuse_callback_handler(
        trace_name=trace_name,
        session_id=thread_id,
        user_id=user_id,
        tags=extra_tags,
        metadata=extra_metadata,
    )
    if not handler:
        return config

    # Standardized tags
    tags = ["blucare", "langgraph", "medical-rag", "groq", settings.app_env]
    if extra_tags:
        tags.extend(extra_tags)
    tags = list(set(tags))

    # Sanitized metadata with langfuse-specific keys for root trace attributes
    clean_meta = sanitize_trace_metadata(extra_metadata or {})
    clean_meta.update({
        "langfuse_session_id": thread_id,
        "langfuse_user_id": user_id,
        "langfuse_trace_name": trace_name,
        "langfuse_tags": tags,
        "app_env": settings.app_env,
        "groq_model": settings.groq_model,
        "embedding_model": settings.embedding_model_name,
        "reranker_model": settings.reranker_model_name,
    })

    config["callbacks"] = [handler]
    config["tags"] = tags
    config["metadata"] = clean_meta

    return config


def flush_langfuse():
    """Safely flushes all pending background events to Langfuse."""
    if not is_langfuse_enabled():
        return
    try:
        from langfuse import get_client
        client = get_client()
        if client:
            client.flush()
            logger.info("Langfuse event queue flushed successfully.")
    except Exception as e:
        logger.debug("Langfuse flush notice: %s", e)


def shutdown_langfuse():
    """Safely shuts down Langfuse client background threads."""
    if not is_langfuse_enabled():
        return
    try:
        from langfuse import get_client
        client = get_client()
        if client:
            client.shutdown()
            logger.info("Langfuse client shut down.")
    except Exception as e:
        logger.debug("Langfuse shutdown notice: %s", e)
