# BluCare+ — Langfuse Setup & Configuration Guide

This guide describes how to configure, verify, and monitor Langfuse for BluCare+.

---

## 1. Environment Configuration

All Langfuse settings are loaded via `.env` in the project root:

```bash
# --- Langfuse Observability & Tracing ---
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY="pk-lf-7f95c698-75cc-46c5-9ac0-f671e8b7114b"
LANGFUSE_SECRET_KEY="sk-lf-2d0f30e9-f97e-4a37-936f-4d1c5450daf0"
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"
```

### Parameter Reference

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `LANGFUSE_ENABLED` | boolean | `false` | Master toggle. Set to `true` to trace patient sessions and RAG queries. |
| `LANGFUSE_PUBLIC_KEY` | string | `""` | Project Public Key (`pk-lf-...`) from Langfuse Cloud Project Settings. |
| `LANGFUSE_SECRET_KEY` | string | `""` | Project Secret Key (`sk-lf-...`) used for server-side event authentication. |
| `LANGFUSE_BASE_URL` | URL | `https://us.cloud.langfuse.com` | Base URL of the Langfuse Cloud instance or self-hosted deployment. |

---

## 2. MCP Server Configuration (IDE & AI Agent Access)

Langfuse provides a native Model Context Protocol (MCP) server that allows developer agents to query prompts, metrics, traces, and datasets.

The server is configured in your MCP configuration file (`mcp_config.json`):

```json
{
  "mcpServers": {
    "langfuse": {
      "url": "https://us.cloud.langfuse.com/api/public/mcp",
      "serverUrl": "https://us.cloud.langfuse.com/api/public/mcp",
      "headers": {
        "Authorization": "Basic cGstbGYtN2Y5NWM2OTgtNzVjYy00NmM1LTlhYzAtZjY3MWU4YjcxMTRiOnNrLWxmLTJkMGYzMGU5LWY5N2UtNGEzNy05MzZmLTRkMWM1NDUwZGFmMA=="
      },
      "disabled": false
    }
  }
}
```

*Note: The Authorization header is `Basic <base64(LANGFUSE_PUBLIC_KEY:LANGFUSE_SECRET_KEY)>`.*

---

## 3. How to Enable or Disable Tracing

- **To Disable Tracing**: Set `LANGFUSE_ENABLED=false` in `.env` (or unset it).
  - The application will execute 100% normally.
  - Zero network calls to Langfuse will be made.
- **To Enable Tracing**: Set `LANGFUSE_ENABLED=true` in `.env` and restart the backend server.

---

## 4. Navigating the Langfuse Dashboard

1. Log in to [Langfuse Cloud (US Region)](https://us.cloud.langfuse.com).
2. Select your project: **BluCare+ / cmwgg2o7n0244ad0inuqxgo9t**.
3. Go to **Tracing -> Traces**:
   - **Filter by Name**:
     - `blucare-triage-request`: Production patient chat turns and triage flows.
     - `ragas_eval_case`: Offline RAG evaluation benchmark runs.
   - **Filter by Tags**:
     - `blucare`, `langgraph`, `medical-rag`, `groq`, `development`, `production`.
     - `ragas-evaluation` for offline benchmarks.
   - **Filter by Session ID**:
     - Enter the session `thread_id` to inspect the complete conversation history turn-by-turn.
4. Drill down into any trace:
   - Click on nodes (`safety_assessment`, `retrieve_medical_evidence`, `cross_encoder_rerank`, `differential_assessment`) to view duration waterfalls, input symptoms, retrieved medical IDs, and Groq token metrics.

