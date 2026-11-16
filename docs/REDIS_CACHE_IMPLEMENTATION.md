# BluCare+ — Redis Semantic Cache Implementation Architecture

## 1. Executive Summary & Purpose
BluCare+ is an AI-assisted clinical decision-support and medical triage system designed to assist patients in understanding health symptoms while connecting them to verified care pathways. Prior to this enhancement, every user request—whether a clinical triage interaction or an identical/paraphrased medical inquiry (e.g., *"What is migraine?"*)—invoked an end-to-end RAG pipeline: embedding generation, dense vector retrieval from Qdrant, CrossEncoder reranking (`BAAI/bge-reranker-base`), prompt assembly, and inference against the Groq Llama 3.3 70B LLM.

Repeated LLM generation for standard educational medical questions introduced:
1. **Unnecessary Latency**: 2.5s–10s per query depending on token generation length and provider queue depth.
2. **Third-Party API Rate Limits**: Groq per-minute request (RPM) and token (TPM) quota depletion.
3. **Redundant Compute Costs**: Repeated embedding, cross-encoding, and LLM token processing for static clinical reference information.

We introduced **Redis Semantic Caching** as a non-invasive, fast-path caching layer around BluCare+. The cache intercepts eligible general medical inquiries, performs semantic vector lookup using our existing **BAAI/bge-small-en-v1.5** embedding model, and delivers verified responses in **~20ms–35ms** while strictly bypassing active clinical triage, emergency triage, and patient-specific medical decisions.

---

## 2. Architectural Data Flow & Pipeline Integration

The semantic caching layer operates upstream of the LangGraph triage workflow without disrupting medical reasoning or safety logic:

```
                          Incoming Patient Request
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │  Deterministic Eligibility   │
                      │         Classifier          │
                      └──────────────┬──────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
         [INELIGIBLE]                                [ELIGIBLE]
                 │                                       │
                 ▼                                       ▼
    ┌─────────────────────────┐             ┌─────────────────────────┐
    │ Direct Bypass to        │             │ Query Normalization &   │
    │ LangGraph / Safety      │             │ BGE Vector Embedding    │
    │ Engine Pipeline         │             └────────────┬────────────┘
    └─────────────────────────┘                          │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ Redis Cosine Distance   │
                                            │ Similarity Lookup (≤0.08│
                                            └────────────┬────────────┘
                                                         │
                                        ┌────────────────┴────────────────┐
                                        │                                 │
                                   [CACHE HIT]                       [CACHE MISS]
                                        │                                 │
                                        ▼                                 ▼
                           ┌─────────────────────────┐       ┌─────────────────────────┐
                           │ Validate Metadata & TTL │       │ LangGraph RAG Workflow  │
                           │ Return Cached Response  │       │ (Qdrant + Groq LLaMA)   │
                           │ Track in Langfuse       │       └────────────┬────────────┘
                           └─────────────────────────┘                    │
                                                                          ▼
                                                             ┌─────────────────────────┐
                                                             │ Store Result in Redis   │
                                                             │ with TTL & Metadata     │
                                                             └─────────────────────────┘
```

---

## 3. What Can Be Cached: Strict Eligibility vs Safety Bypass

In a clinical triage application, incorrect caching poses severe patient safety risks. The cache enforces a **deterministic allowlist/denylist filter**:

### 3.1 Allowed: General Educational Medical Knowledge
Only standalone, non-personalized educational inquiries are eligible for semantic caching:
- *"What is migraine?"* / *"What is a migraine headache?"*
- *"What is tension headache?"* / *"What is tension type headache?"*
- *"What causes viral fever?"* / *"What is the cause of viral fever?"*
- *"What are common symptoms of migraine?"*
- *"What is the difference between viral and bacterial pharyngitis?"*

### 3.2 Prohibited & Bypassed: Clinical Triage & Safety Invariants
The cache strictly bypasses and delegates to the core safety and clinical triage engine under any of the following conditions:
1. **Emergency & Red-Flag Triggers**: Any phrase matching the BluCare+ `SafetyEngine` rules (chest pain, stroke signs, anaphylaxis, severe dyspnea, suicide risk) triggers immediate emergency response.
2. **Multi-Turn Sessions (`turn_id > 1`)**: Active diagnostic conversations depend on earlier clinical context and must never replay isolated cached snippets.
3. **Active Patient Case Context**: If the user's session already has recorded symptoms, duration, or severity, the cache is bypassed.
4. **First-Person Pronouns**: Queries containing `"I"`, `"me"`, `"my"`, `"myself"`, or `"we"` indicate personal patient presentation rather than generic inquiry.
5. **Temporal Onset & Durations**: Queries mentioning `"since yesterday"`, `"for 3 days"`, `"started 2 hours ago"` signify an active clinical episode.
6. **Severity Qualifiers**: Words like `"severe"`, `"mild"`, `"unbearable"`, `"excruciating"`, or `"worsening"` indicate an individual symptom complaint.
7. **Medication & Dosage Requests**: Queries asking about milligrams, pills, tablets, or specific drug dosages (e.g., paracetamol, ibuprofen, antibiotics) are bypassed to prevent improper self-medication.
8. **Sensitive Clinical Contexts**: Mentions of pregnancy, pediatrics, diabetes, hypertension, cardiac history, or organ failure bypass the cache.
9. **Ambiguous Intent Fallback**: When intent cannot be conclusively determined as educational, BluCare+ prioritizes medical safety over cache hit rate and bypasses caching.

---

## 4. Vector Embedding & Redis Semantic Matching

### 4.1 Embedding Reuse (Zero Additional Overhead)
Rather than downloading a separate 400MB model or calling a paid embedding API, the semantic cache directly reuses the existing in-memory **`BAAI/bge-small-en-v1.5`** model:
- **Dimensions**: 384
- **Pooling**: Mean pooling with normalization
- **Memory Footprint**: Shared singleton with the primary retrieval service (`app.rag.store.embed_query`)

### 4.2 Cosine Distance Metric Calibration
RedisVL and vector distance metrics use **cosine distance** $D = 1.0 - \text{CosineSimilarity}(\mathbf{u}, \mathbf{v})$:
- $D = 0.0$: Identical query
- $D \le 0.08$: Close semantic paraphrase (e.g., *"What is migraine?"* vs *"What is a migraine headache?"* $\to D = 0.0229$)
- $D > 0.12$: Distinct medical conditions (e.g., *"What is viral pharyngitis?"* vs *"What is streptococcal pharyngitis?"* $\to D = 0.1366$)
- $D > 0.25$: Completely different medical topics (e.g., *"What is migraine?"* vs *"What is tension headache?"* $\to D = 0.2553$)

A conservative threshold of **`REDIS_CACHE_DISTANCE_THRESHOLD=0.08`** ensures that paraphrased inquiries achieve high hit rates while dissimilar clinical entities never cross-contaminate.

---

## 5. Cache Schema, Metadata & Invalidation

Each cached entry is stored in Redis under the key namespace `blucare:cache:doc:<uuid>` with a dual-lookup structure:

```json
{
  "query": "what is migraine",
  "normalized_query": "what is migraine",
  "response": "**Clinical Triage Assessment:** ...",
  "sources_json": "[{\"title\": \"Clinical Diagnosis of Acute Migraine\", \"document_id\": \"REF-01\"}]",
  "corpus_version": "curated_kb_v1.0",
  "synthesis_prompt_version": "v1.0.0",
  "embedding_model": "BAAI/bge-small-en-v1.5",
  "generation_model": "llama-3.3-70b-versatile",
  "created_at": "1731610800.0",
  "expires_at": "1731632400.0",
  "vector": "<384-dimensional float32 byte array>"
}
```

### Invalidation Triggers
A cached entry is treated as a **cache miss** and discarded if:
1. **TTL Expiration**: Default TTL is 6 hours (`REDIS_CACHE_TTL_SECONDS=21600`).
2. **Corpus Version Mismatch**: If `settings.corpus_version` changes, old entries are invalidated.
3. **Prompt Version Mismatch**: If `settings.synthesis_prompt_version` changes, clinical synthesis rules have evolved.
4. **Missing or Corrupted Citations**: Entries missing valid source attribution are rejected.

---

## 6. Resilience & Graceful Degradation
Redis semantic caching is designed as a **strictly optional optimization layer**:
- If Redis is unreachable or times out (socket timeout: 1.5s), the application catches the error, logs a diagnostic warning, and proceeds through the full RAG pipeline.
- Under zero circumstances will a Redis connection failure cause an HTTP 500 or drop a patient triage request.
- Tested and verified via unit test `test_scenario_12_redis_unavailable_resilience`.

---

## 7. Langfuse Observability Integration
Cache operations are recorded into existing Langfuse trace spans without creating a duplicate telemetry silo:
- `cache_hit`: `True` / `False`
- `cache_distance`: Cosine distance metric for hit analysis
- `llm_calls_avoided`: `1` for hits, `0` for misses/bypasses
- `tokens_avoided`: Estimated tokens saved (~1,700 tokens per Groq call)
- `lookup_duration_s`: Real execution latency of Redis vector lookup (~0.020s)
- Sensitive user health data is never logged to Redis keys or Langfuse metadata.

