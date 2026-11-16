# BLUCARE+ — IMPLEMENT REDIS SEMANTIC CACHING

## Main objective

Implement Redis-based semantic caching in our existing BluCare+ project.

The purpose is to reduce unnecessary repeated computation, avoid repeated LLM calls for eligible general medical questions, improve response speed and reduce API usage.

Keep everything simple and suitable for a final-year engineering internship project.

**Do not rebuild our existing application or RAG pipeline. Add Redis as an optional caching layer around the existing implementation.**

## 1. Understand our existing project first

Inspect the existing backend and understand:

- FastAPI endpoints.
- LangGraph workflow.
- Existing BGE embedding model.
- Qdrant retrieval.
- CrossEncoder reranking.
- Groq generation.
- Medical answer-generation prompts.
- Langfuse tracing.
- RAGAS evaluation.
- Existing environment configuration and Docker Compose setup.

Also inspect:

- Original RAGAS baseline results.
- Improved RAGAS results, if available.
- Langfuse traces and actual latency information.
- Which operations consume the most time.
- Which LLM requests are repeated frequently.

Use this information to decide where caching can provide a real benefit.

Do not introduce caching simply because it is available.

## 2. Choose a suitable Redis implementation

Use:

- Redis for cache storage.
- RedisVL SemanticCache for semantic similarity lookup, where compatible with our existing dependencies.
- Our existing BGE embedding model wherever practical.

Important requirements:

- Reuse the existing embedding model.
- Do not introduce another paid embedding API.
- Preserve the existing 384-dimensional vector configuration if that is what the current BGE model uses.
- Avoid downloading another embedding model unnecessarily.
- Check Python dependency compatibility before installation.
- Follow the current official RedisVL documentation.

Official references:

https://redis.io/docs/latest/develop/use-cases/semantic-cache/

https://docs.redisvl.com/en/latest/api/cache.html

Keep the Redis implementation small and reusable.

## 3. Decide carefully WHAT can be cached

This is the most important part of this implementation.

BluCare+ is a medical triage application. Do not treat every similar question as having the same answer.

### ALLOWED: Safe general medical information

Semantic caching can be used for standalone, non-personalized educational questions such as:

- What is migraine?
- What is a tension headache?
- What is dehydration?
- What are common symptoms of viral pharyngitis?
- What is the difference between a viral and bacterial infection?

For eligible questions:

1. Check Redis before making the expensive generation call.
2. If a valid semantic match exists, return the cached educational response.
3. If no match exists, use the existing RAG pipeline.
4. Generate an evidence-grounded response.
5. Store the response with the relevant metadata and TTL.

The cached response must preserve the original evidence references and must remain valid for the current corpus and prompt versions.

### NOT ALLOWED: Patient-specific medical decisions

Never cache or replay:

- Patient-specific symptom assessments.
- Differential diagnoses for an individual patient.
- Triage risk or urgency classifications.
- Emergency decisions.
- Personalized medical recommendations.
- Medication dosages.
- Treatment decisions.
- Ayurvedic prescriptions or personalized remedies.
- Responses depending on age, allergies, medication history, pregnancy or medical conditions.
- Responses depending on earlier messages in a conversation.

For example:

"I have had fever for two days."

This must never receive another patient's cached assessment.

"Which paracetamol dosage should I take?"

This must bypass semantic response caching.

"Am I experiencing a dangerous headache?"

This must bypass semantic response caching.

### Important bypass rule

If the request is part of an active patient assessment, contains patient-specific information, depends on conversation history, or its intent is uncertain, bypass the response cache.

The existing safety engine must execute normally on every relevant patient interaction.

**When uncertain, bypass caching. Medical correctness is more important than cache hit rate.**

Do not add a complicated new AI classifier just to determine cache eligibility. Use existing request context and simple deterministic checks. If eligibility cannot be established safely, treat the request as ineligible.

## 4. Implement the semantic cache flow

For eligible general educational requests, implement this flow:

Incoming request
→ Cache eligibility check
→ Prepare normalized cache query
→ Generate query embedding using existing BGE
→ Redis semantic similarity lookup
→ Validate matching entry and metadata
→ Cache hit: return valid cached educational response
→ Cache miss: execute existing RAG retrieval and generation
→ Validate generated answer and citations
→ Store safe result in Redis
→ Return response

Preserve the existing response structure and frontend API contract.

Do not make the cache responsible for clinical reasoning or safety decisions.

### Similarity threshold

Use a conservative threshold initially and tune it through testing.

Important: RedisVL's `distance_threshold` represents cosine distance, not cosine similarity. Lower distance values mean stricter matching.

Do not blindly configure `0.95` as the distance threshold.

Calibrate the threshold against actual similar and dissimilar medical questions. Measure incorrect cache matches before allowing a cache hit.

Reference:

https://redis.io/docs/latest/develop/ai/redisvl/api/cache/

## 5. Cache metadata and invalidation

Every cached entry must contain enough metadata to verify that it is still valid.

Include:

- Original normalized question.
- Cached response.
- Relevant source document IDs.
- Embedding model/version.
- Generation model/version.
- Prompt version.
- Medical corpus or corpus-version identifier.
- Cache category.
- Creation timestamp.
- Expiration timestamp.

Use a configurable TTL. Start conservatively, for example six hours, and adjust only after testing.

Invalidate or separate entries when:

- The medical corpus changes.
- Relevant source documents are updated.
- The generation prompt changes.
- The embedding model changes.
- The generation model changes.
- The cache schema changes.

Do not return stale medical information simply because its vector similarity is high.

Do not store patient messages, patient history, personal identifiers or complete patient assessment records in Redis.

## 6. Integrate with existing Langfuse

We already have Langfuse observability.

Reuse that integration.

Record cache-related information such as:

- Cache hit or miss.
- Cache bypass.
- Cache bypass reason.
- Similarity distance.
- Cache lookup duration.
- Cache storage duration.
- Redis errors.
- LLM calls avoided.
- Tokens avoided, only when actual token usage is known.

Make cache activity visible in the existing Langfuse traces.

Do not create a second observability platform.

Do not log sensitive patient questions or cached medical records.

## 7. Redis configuration

Add simple environment configuration:

```env
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_ENABLED=false
REDIS_CACHE_TTL_SECONDS=21600
REDIS_CACHE_DISTANCE_THRESHOLD=0.05
```

These are initial example values, not guaranteed optimal settings. Verify the correct threshold behavior using the installed RedisVL version.

Requirements:

- Redis must be optional.
- The application must work normally when caching is disabled.
- If Redis is unavailable, continue through the existing RAG pipeline.
- A Redis connection failure must never cause a patient request to fail.
- Do not expose Redis credentials.
- Do not commit real environment values.
- Do not introduce a paid Redis service.
- Use a simple local Redis setup through the existing development environment or Docker Compose.

Do not create a complex Redis cluster or additional infrastructure for this student project.

## 8. Testing and performance comparison

Test both cache-enabled and cache-disabled behavior.

Create tests for:

1. First eligible general question: cache miss.
2. Repeated identical general question: cache hit.
3. Semantically similar eligible question: cache hit only when the match is sufficiently close.
4. Different medical topic: cache miss.
5. Similar wording but different clinical meaning: cache miss.
6. Active patient assessment: cache bypass.
7. Personalized dosage question: cache bypass.
8. Emergency-related question: cache bypass.
9. Patient history or sensitive context: cache bypass.
10. Expired cache entry: cache miss.
11. Changed corpus or prompt version: invalid entry is not reused.
12. Redis unavailable: existing application still works.
13. Invalid cached metadata or citation: cache miss.

Verify the actual returned response, not just the Redis hit counter.

### Performance benchmark

Use a set of representative synthetic general medical questions.

Run:

- Cache disabled.
- Cache enabled with an empty cache.
- Cache enabled with a warmed cache.

Measure:

- Cache hit rate.
- Cache miss rate.
- Cache lookup latency.
- Average response latency.
- p50 and p95 latency when enough test samples exist.
- Number of LLM calls avoided.
- Token usage avoided, when available.

Use real measured data.

Do not claim that Redis always provides under-50ms latency. Measure it on our actual environment.

Also verify that cache-enabled responses remain correct and grounded.

## 9. RAGAS quality verification

Preserve all previous RAGAS datasets, original baseline results and improved experiment results.

Never overwrite or delete previous reports.

Use the existing golden dataset to verify that Redis has not weakened our system.

Run two clearly separated evaluations:

1. Cache disabled — original RAG evaluation behavior.
2. Cache enabled — eligible cache behavior and normal RAG fallback.

For clinical triage and patient-specific evaluation cases, cache must be bypassed.

For safe educational questions, verify cached answers against their original evidence and valid source references.

Record any differences.

Do not modify the RAG prompts, retrieval parameters, corpus or safety engine merely to improve cache results.

## 10. Keep the implementation simple

Do not introduce:

- A new AI agent.
- A second embedding provider.
- Another vector database.
- Langfuse replacement.
- Arize Phoenix.
- Kubernetes.
- Complex cache-management services.
- A new backend architecture.
- Unnecessary frontend changes.

Use existing FastAPI, LangGraph, Qdrant, BGE, CrossEncoder, Groq and Langfuse components.

The cache should be one small, optional module integrated into the appropriate existing request path.

## 11. Preserve results for internship interviews

Create:

`REDIS_CACHE_IMPLEMENTATION.md`

`CACHE_BENCHMARK_REPORT.md`

`CACHE_TEST_REPORT.md`

`INTERVIEW_NOTES.md`

Preserve the existing RAGAS and Langfuse reports.

Document:

- Why we introduced semantic caching.
- Which requests are eligible.
- Which medical requests are intentionally bypassed.
- How Redis semantic matching works.
- How the existing BGE model is reused.
- How cache invalidation works.
- Actual cache hit rate.
- Actual latency before and after caching.
- Actual LLM calls and tokens avoided.
- Limitations and trade-offs.

Prepare five simple technical interview questions and answers based on the implementation.

Include an honest resume achievement only after obtaining real benchmark results.

## 12. Final acceptance criteria

Implementation is complete only when:

1. Redis connects successfully.
2. Semantic caching works for eligible general educational questions.
3. Repeated eligible queries can return valid cached responses.
4. Patient-specific medical decisions always bypass response caching.
5. Emergency safety behavior remains unchanged.
6. Invalid and expired entries are rejected.
7. Redis failure does not break BluCare+.
8. Langfuse records cache activity.
9. Existing RAGAS results remain preserved.
10. Cache performance is measured and documented.
11. Tests confirm correct behavior for both hits and bypasses.
12. Existing application functionality continues to work.

## FINAL INSTRUCTION

I want a real working Redis semantic cache, not just Redis installed in Docker.

Use it intelligently in BluCare+.

Reduce repeated LLM work for safe, reusable medical educational questions while protecting personalized patient assessments.

Keep it simple, fast, reliable and understandable.

Do not change the existing RAG architecture unnecessarily. Do not proceed to additional optimization projects after completing this phase.