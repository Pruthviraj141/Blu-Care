# BLUCARE+ — IMPLEMENT LANGFUSE OBSERVABILITY & TRACING

## Main objective

Integrate Langfuse into our existing BluCare+ application to monitor and understand the actual execution of our LLM and LangGraph pipeline.

I want to see:

- What happens during each patient interaction.
- Which LangGraph nodes execute.
- How much time each node takes.
- Which LLM calls are made.
- How long Groq generation takes.
- How much retrieval and reranking take.
- Token usage when available.
- Where errors occur.
- Which parts of our RAG pipeline need improvement.

Keep the implementation simple and suitable for a final-year engineering internship project.

**Do not rebuild our architecture. Integrate Langfuse into the existing code.**

## 1. First understand the existing project

Inspect the current backend and identify:

- FastAPI endpoints.
- LangGraph graph construction and invocation.
- All existing graph nodes.
- Symptom extraction.
- Safety checks.
- Question planning.
- Qdrant retrieval.
- BGE embedding generation.
- CrossEncoder reranking.
- Medical context construction.
- Groq LLM calls.
- Final answer generation.
- Citation validation.
- Session management.
- Streaming responses.

Understand how the actual application executes before adding instrumentation.

Do not assume node names or function names. Use the existing source code.

## 2. Integrate Langfuse using the compatible official SDK

Use the official Langfuse Python SDK and its LangChain/LangGraph integration.

Official documentation:

https://langfuse.com/docs/observability/sdk/overview

https://langfuse.com/integrations/frameworks/langgraph

Requirements:

- Inspect installed versions of LangChain, LangGraph and LangChain Core first.
- Use the official Langfuse API compatible with those versions.
- Check the current SDK documentation before implementation.
- Avoid deprecated SDK APIs.
- Do not mix old and new Langfuse client patterns.
- Keep the existing Groq integration unchanged.
- Do not replace the LLM provider.

Create a small reusable Langfuse initialization module.

Initialize the client once rather than creating a new client for every request.

## 3. Connect tracing to actual LangGraph execution

This is the most important part.

Instrument the existing graph execution using the official Langfuse callback integration.

Make sure callbacks are correctly passed through the actual graph invocation, including:

- Normal graph invocation.
- Asynchronous invocation, where used.
- Streaming graph execution.
- Nested LangChain and LLM calls.

I want each patient interaction to appear as an understandable trace in Langfuse.

Organize traces using meaningful names and tags.

For example:

`blucare-triage-request`

Tags:

- blucare
- langgraph
- medical-rag
- groq
- production or evaluation

Use the actual environment and execution type for tagging.

Each trace should be associated with an opaque session identifier where appropriate. Do not expose Clerk credentials, access tokens or personally identifying information.

## 4. Capture important execution stages

Make sure the following stages are visible in Langfuse wherever they exist in our current execution path.

### A. Symptom extraction

Capture:

- Execution start and end.
- Duration.
- Success or failure.
- Sanitized execution metadata.

### B. Safety checks

Capture:

- Safety-check execution.
- Duration.
- Whether the safety engine completed successfully.
- Error information if it fails.

Do not log sensitive patient details or allow tracing to change safety decisions.

### C. Question planning

Capture:

- Question-planner execution.
- Duration.
- Whether a question was generated.
- Execution errors.

### D. Medical RAG retrieval

Capture:

- Query-construction execution.
- Embedding execution.
- Qdrant retrieval duration.
- Number of retrieved chunks.
- Relevant non-sensitive document IDs.
- Retrieval failures.

### E. CrossEncoder reranking

Capture:

- Reranking duration.
- Number of chunks before and after reranking.
- Final selected document IDs.
- Errors.

### F. Answer generation

Capture:

- Groq model name.
- Generation duration.
- Token usage when returned by the provider.
- Model-call errors.
- Completion status.

### G. Citation validation

Capture:

- Number of citations checked.
- Number of valid citations.
- Number of invalid citations.
- Validation errors.

Do not fabricate token usage, cost or timing information.

If the provider does not expose token usage or reliable pricing, report it as unavailable rather than estimating it.

## 5. Add custom spans only where necessary

The Langfuse callback should capture existing LangChain and LangGraph execution automatically where supported.

For custom Python operations that are not captured automatically, add small custom spans using the current official SDK.

Examples:

- Custom query construction.
- Custom Qdrant operations.
- CrossEncoder execution.
- Citation validation.
- Other important non-LLM processing.

Avoid creating excessive spans for every small helper function.

The goal is a useful execution trace, not hundreds of meaningless entries.

Use understandable names such as:

- `symptom_extraction`
- `safety_check`
- `query_construction`
- `embedding_generation`
- `qdrant_retrieval`
- `cross_encoder_reranking`
- `context_assembly`
- `groq_generation`
- `citation_validation`

Use actual names when they differ in the repository.

## 6. Capture performance and token usage

I want to understand which component is consuming the most time.

For every request, capture:

- Total execution duration.
- Duration per important node.
- Qdrant retrieval duration.
- Reranking duration.
- LLM generation duration.
- Token usage when available.
- Error count.
- Successful and failed executions.

Use the provider's actual token-usage metadata whenever available.

Cost should only be shown when reliable pricing information is configured for the actual model. Never invent costs.

## 7. IMPORTANT — Protect medical and user data

BluCare+ handles potentially sensitive health information.

Do not send unrestricted patient data to Langfuse.

By default:

- Do not log names, email addresses, phone numbers or addresses.
- Do not log Clerk access tokens or API keys.
- Do not log full medical conversation histories.
- Do not log raw patient messages or complete patient records.
- Do not log full retrieved medical contexts containing patient-specific information.
- Do not include personally identifying information in trace names or tags.

Prefer:

- Opaque session identifiers.
- Node names.
- Model names.
- Timing information.
- Token counts.
- Document IDs.
- Error categories.
- Non-sensitive configuration metadata.

If inputs or outputs are necessary for debugging, use explicitly controlled redaction and sanitization. Synthetic evaluation examples may be traced separately.

Make sure secrets and patient information never appear in logs or exception tracebacks sent to Langfuse.

## 8. Keep Langfuse optional and safe

Add environment-based configuration.

Use:

- `LANGFUSE_ENABLED`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL`

Add placeholder entries to `.env.example`.

Never commit actual credentials.

Requirements:

- Langfuse must be optional.
- If disabled, BluCare+ must work normally.
- If credentials are unavailable, the application must not crash.
- If Langfuse is temporarily unreachable, patient requests must still work.
- Instrumentation must not block the main response unnecessarily.
- Do not make synchronous tracing requests inside every patient interaction.
- Ensure events are flushed correctly during application shutdown.

Use the official SDK's supported background processing and lifecycle methods.

Do not expose the secret key or initialize Langfuse in frontend JavaScript.

## 9. Connect tracing with our RAGAS evaluation

We previously implemented RAGAS evaluation and have baseline and improvement experiment results.

Preserve all previous RAGAS reports and experiment files.

Do not overwrite or modify them.

Optionally, add Langfuse traces for evaluation runs using a clear tag such as:

`ragas-evaluation`

For evaluation traces, associate:

- Evaluation run ID.
- Test-case ID.
- Dataset version.
- RAG configuration.
- Actual retrieval and generation timings.

Use synthetic evaluation questions only.

Keep production patient traces and offline evaluation traces distinguishable.

Langfuse is for observing execution. RAGAS remains responsible for evaluating retrieval and generation quality.

Do not rebuild the existing RAGAS framework.

## 10. Testing

Test the real BluCare+ application.

Run several test interactions:

1. A simple greeting.
2. A normal symptom assessment.
3. A question that triggers medical RAG.
4. A question with insufficient medical evidence.
5. An error case, where safely reproducible.
6. A streaming response.

For each interaction, verify:

- A trace is generated when enabled.
- The trace contains the actual graph execution.
- Important stages are visible.
- Durations are recorded.
- LLM calls are captured.
- Errors are visible.
- No sensitive patient information is leaked.
- The patient-facing response remains unchanged.

Also test with Langfuse disabled and with invalid credentials.

BluCare+ must continue functioning in both cases.

## 11. Keep the implementation simple

Do not install or introduce:

- Arize Phoenix.
- Redis.
- OpenTelemetry infrastructure independently unless required by the current official Langfuse integration.
- Another monitoring platform.
- Additional agents.
- New databases for application logic.
- Kubernetes.
- Unnecessary Docker services.

Do not introduce a complex microservice architecture.

Use the existing FastAPI, LangGraph, Groq and Qdrant architecture.

For the initial setup, prefer the simplest suitable Langfuse deployment. Use Langfuse Cloud or an already available self-hosted setup. Do not add a heavy self-hosted infrastructure stack without demonstrating that it is necessary.

## 12. Final deliverables

Create:

- `LANGFUSE_IMPLEMENTATION.md`
- `LANGFUSE_SETUP.md`
- `LANGFUSE_TEST_REPORT.md`

Document:

1. How Langfuse was integrated.
2. Which actual nodes and operations are traced.
3. How to configure credentials.
4. How to enable or disable tracing.
5. How to find BluCare+ traces in the dashboard.
6. Which metrics and token-usage information are available.
7. How sensitive information is protected.
8. What testing was actually performed.

Provide a simple diagram:

FastAPI Request → LangGraph → Individual Nodes → RAG Retrieval → Reranking → Groq Generation → Response

Show how Langfuse observes this flow.

At completion, summarize:

- Files changed.
- SDK versions used.
- Tracing stages implemented.
- Successful test count.
- Example trace structure.
- Available latency and token metrics.
- Any unsupported token-cost tracking.
- Any remaining issues.

## FINAL REQUIREMENT

I want to open the Langfuse dashboard and understand exactly what happens when BluCare+ processes a request.

I should be able to identify slow nodes, failed retrievals, expensive LLM calls and execution errors without digging through hundreds of terminal logs.

Keep it simple, functional and reliable.

Do not modify our medical RAG logic or optimize the system in this phase. This phase is only for observability and tracing.