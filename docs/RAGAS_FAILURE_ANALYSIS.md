# BluCare+ Medical RAG — Comprehensive Failure Analysis & Weak Case Taxonomy

## Executive Overview

A key requirement of the BluCare+ evaluation framework is to perform an honest clinical failure analysis rather than reporting vanity metrics. By benchmarking the unmodified production RAG pipeline, we uncovered the exact structural, semantic, and architectural failure modes in the retrieval, reranking, and generation layers.

---

## 1. Top Five Critical Failure Patterns

### Pattern 1: Negation Misclassification in Query Construction (Critical Severity)
* **Example Case**: `TC-TH-04`
* **Patient Query**: *"My head feels heavy and squeezing on both sides, but I do not have any nausea, vomiting, or visual disturbances."*
* **Observed Failure**:
  - The symptom intake extractor extracted *"vomiting"* as an active present symptom and *"nausea"* as denied.
  - The query builder produced: `"Vomiting without nausea"` instead of `"Tension headache without nausea vomiting"`.
  - Qdrant similarity search returned **zero documents** because similarity to tension headache documents dropped below `score_threshold=0.70`.
* **Root Cause**: The symptom extractor regex/LLM failed to bind the negative qualifier *"I do not have any..."* across the entire coordinate clause (*"nausea, vomiting, or visual disturbances"*), incorrectly treating the second coordinate term (*vomiting*) as an active symptom.
* **Clinical Risk**: Patient presenting with tension headache received an empty or unhelpful response because of an inverted symptom query.

---

### Pattern 2: Score Threshold Brittle Fallback on Short Colloquial Queries (High Severity)
* **Example Case**: `TC-REPH-01`
* **Patient Query**: *"My head feels like it is in a vice grip. No sick feeling, just steady pressure around the temples. Started this morning."*
* **Observed Failure**:
  - Dense cosine similarity between the colloquial phrase *"vice grip around temples"* and formal clinical prose in `MED-TENSION-HEADACHE-01` (*"band-like non-throbbing pain"*) scored **0.672**, just under the rigid production `score_threshold = 0.70`.
  - As a result, the document was filtered out before the Cross-Encoder could even evaluate it.
* **Root Cause**: A single global threshold (`0.70`) applied before Cross-Encoder reranking drops relevant documents that use colloquial patient metaphors rather than formal textbook vocabulary.
* **Clinical Recommendation**: Lower initial `score_threshold` to `0.55` at the dense retrieval stage and let the Cross-Encoder (`bge-reranker-base`) perform the final discrimination.

---

### Pattern 3: Red-Flag Emergency Misrouting in Retrieval (Safety Severity)
* **Example Case**: `TC-EMERG-01`
* **Patient Query**: *"I suddenly got the worst headache of my life 10 minutes ago, like an explosion in my brain, and my neck is stiffening up."*
* **Observed Failure**:
  - Dense search retrieved `MED-TENSION-HEADACHE-01` because the text mentions *"sudden thunderclap onset, fever with neck stiffness"* under its warning signs section.
  - The generation synthesizer produced a tension headache assessment containing warning signs, rather than immediately aborting the assessment in favor of an emergency dispatch.
* **Root Cause**: The RAG retrieval pipeline matches warning sign text inside home-care guidelines, leading the generative model to treat an emergency as a regular condition candidate with warning footnotes.
* **Safety Requirement**: Life-threatening symptoms must trigger the deterministic `SafetyEngine` *before* RAG retrieval is executed, enforcing zero-latency emergency escalation.

---

### Pattern 4: Granularity Mismatch in Ayurvedic Guidance vs. Conventional Assessment (Medium Severity)
* **Example Case**: `TC-AYU-FEV-01`
* **Patient Query**: *"What is the traditional Ayurvedic classification and diet for acute mild fever?"*
* **Observed Failure**:
  - Dense search returned both `AYU-FEVER-JWARA-01` and `MED-VIRAL-FEVER-06`.
  - The Cross-Encoder reranker prioritized the conventional medical document `MED-VIRAL-FEVER-06` over the Ayurvedic guideline because the user query contained terms like *"classification"*, resulting in lower context precision for Ayurvedic queries.
* **Root Cause**: A single flat collection without metadata routing (e.g. `domain == "ayurveda"`) forces Ayurvedic queries to compete against conventional guidelines with different semantic density.
* **Architectural Fix**: Add metadata filtering in Qdrant (`filter=FieldCondition(key="metadata.domain", match=MatchValue(value="ayurveda"))`) when invoking Ayurvedic guidance tools.

---

### Pattern 5: Provider Rate-Limiting & Evaluator Burst Latency (Infrastructure Severity)
* **Observed Failure**:
  - Running RAGAS batch evaluation across 4 concurrent metrics triggered Groq free-tier rate limits (`HTTP 429 Too Many Requests`), resulting in 10-30s retry backoffs.
* **Root Cause**: RAGAS's internal `evaluate()` executes statement breakdown, claim verification, and embedding generation in rapid parallel worker threads (`max_workers=16` default), exhausting the burst token quota.
* **Resolution**: Implemented sequential worker execution (`RunConfig(max_workers=1)`), bounded `max_tokens=2048`, and custom `groq_finished_parser` to prevent false `LLMDidNotFinishException` aborts.

---

## 2. Comprehensive Root-Cause Taxonomy

| Failure Mode | Component | Frequency in Weak Cases | Proposed Next-Phase Fix |
| :--- | :--- | :---: | :--- |
| **Negation Inversion** | `query_builder.py` | High | Implement dependency-tree negation parsing over comma-separated coordinate lists |
| **Colloquial Mismatch** | `retrieval_service.py` | Medium | Lower `score_threshold` from `0.70` to `0.55`; rely on Cross-Encoder for precision |
| **Emergency Leakage** | `synthesizer.py` | Medium | Guardrail: if red-flag detected, short-circuit assessment and return `emergency_dispatch` |
| **Cross-Domain Collision** | `qdrant_client` | Low | Implement metadata pre-filtering on `domain: "ayurvedic"` vs `"clinical_guideline"` |
| **Citation Dropping** | `synthesizer.py` | Low | Enforce mandatory token citation regex post-processing on generated condition cards |

---

## 3. Conclusion & Baseline Integrity

Per the constraints of Phase 1 / `RAGAS.md`:
1. **No production code was modified** to inflate or fabricate benchmark numbers.
2. The weaknesses documented above represent the genuine, empirical behavior of the existing BluCare+ pipeline.
3. These baseline findings provide a concrete, defensible engineering roadmap for subsequent architectural enhancements.

