# Complete RAG Pipeline Deep Dive: BluCare+

This document provides a thorough, step-by-step technical explanation of the Retrieval-Augmented Generation (RAG) architecture implemented in BluCare+. Every stage is backed by concrete code references from the repository.

---

## 1. High-Level RAG Architecture

BluCare+ employs a **Two-Stage Retrieve-and-Rerank Pipeline** with strict clinical evidence grounding, citation verification, and conversational state tracking:

```
[Curated Medical Guidelines (WHO, NICE, CDC)]
           │
           ▼
[SHA-256 Hashing & Metadata Enrichment]
           │
           ▼
[BAAI/bge-small-en-v1.5 Pure Passage Embeddings (384d)]
           │
           ▼
[Qdrant Vector DB: collection 'medical_triage_kb' (Cosine)]
════════════════════════════════════════════════════════════
[Patient Query: "throbbing headache 2 days"]
           │
           ▼
[MedicalQueryBuilder: Query Formulation & Intent Classification]
           │
           ▼
[BGE Asymmetric Query Prefix: "Represent this sentence..."]
           │
           ▼
[Stage 1: Qdrant Dense Similarity Search (Cosine >= 0.55, fetch_k=20)]
           │
           ▼
[Stage 2: Cross-Encoder Reranker (BAAI/bge-reranker-base, final_k=5)]
           │
           ▼
[Evidence Context Assembler: Token Budgets, Source Numbering [S1..S5]]
           │
           ▼
[ChatGroq (Qwen 27B / Llama 3): Grounded Differential Assessment]
           │
           ▼
[CitationValidator: Deterministic [MED-xxx] Token Verification]
           │
           ▼
[Pydantic Coercion & PostgreSQL Persistence -> Frontend Delivery]
```

---

## 2. Step 1: Document Ingestion & Preprocessing

**Source File:** [app/rag/document_ingestion.py](file:///home/pruthvi/projects/multiagentrag/app/rag/document_ingestion.py)

### How Knowledge Enters the System
BluCare+ ingests verified clinical triage guidelines from authoritative sources (WHO, NICE, CDC, Ministry of Health) defined in `CURATED_MEDICAL_KNOWLEDGE`:
- `MED-TENSION-HEADACHE-01`: WHO Tension Headache Clinical Diagnosis & Home Care.
- `MED-MIGRAINE-WITHOUT-AURA-02`: NICE Acute Migraine Management (CG150).
- `MED-VIRAL-PHARYNGITIS-03`: CDC Acute Upper Respiratory Infection / Sore Throat.
- `MED-ACUTE-GASTROENTERITIS-04`: WHO Diarrhea & Dehydration Triage.
- `MED-ACUTE-BRONCHITIS-05`: NICE Acute Bronchitis and Cough Guidelines.
- `MED-VIRAL-FEVER-06`: WHO Acute Febrile Illness Management.
- `MED-DENGUE-FEVER-07`: WHO Dengue Warning Signs & Fluid Management.
- `AYU-*-01`: Verified traditional/Ayurvedic wellness guidelines.

### Processing Steps
1. **Cleaning & Trimming:** Whitespace normalization and clinical entity alignment.
2. **Cryptographic Fingerprinting:** A SHA-256 hash of the document content is computed:
   ```python
   content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
   ```
3. **Structured Provenance Metadata:** Wrapped in `MedicalDocumentMetadata` ([app/rag/provenance.py](file:///home/pruthvi/projects/multiagentrag/app/rag/provenance.py)):
   - `document_id`: Canonical identifier (e.g. `MED-MIGRAINE-WITHOUT-AURA-02`).
   - `chunk_id`: E.g. `MED-MIGRAINE-WITHOUT-AURA-02-c1`.
   - `publisher`: "NICE Clinical Guidelines (CG150)".
   - `source_url`: Verifiable clinical reference link.
   - `clinical_topic`: E.g. "Neurology / Migraine".
   - `review_status`: `DocumentReviewStatus.APPROVED`.

4. **Passage Embedding Generation (Critical Nuance):**
   ```python
   # Embedded WITHOUT the query instruction prefix:
   vector = embeddings.embed_documents([content])[0]
   ```
5. **Idempotent Upsert to Qdrant:**
   Generates a deterministic integer point ID from `chunk_id` using MD5, ensuring repeated ingestion runs do not create duplicate points:
   ```python
   point_id = int(hashlib.md5(chunk_id.encode("utf-8")).hexdigest()[:15], 16)
   client.upsert(collection_name="medical_triage_kb", points=points)
   ```

---

## 3. Step 2: Embeddings & Vector Representation

**Source File:** [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py#L78-L127)

### Model Selection: BAAI/bge-small-en-v1.5
- **Dimensionality:** 384 floating-point numbers.
- **Metric:** Cosine distance (`models.Distance.COSINE`).
- **Normalized Vectors:** `encode_kwargs={"normalize_embeddings": True}`. When vectors are normalized to unit length, cosine similarity is equivalent to dot product, speeding up vector index traversal.

### Asymmetric Embeddings Principle
BGE models are trained asymmetrically to distinguish search queries from target documents:
- **Queries:** Require a task prompt instruction prefix:
  ```python
  prefixed = "Represent this sentence for searching relevant passages: " + query_text
  return get_embeddings().embed_query(prefixed)
  ```
- **Passages:** Encoded directly without any prefix.
- *Why this matters in an interview:* If queries are embedded without the instruction, or if passages are accidentally embedded with it, the vectors map to different regions of the latent space, silently destroying retrieval recall!

---

## 4. Step 3: Vector Store (Qdrant)

**Source File:** [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py)

1. **Storage Modes:**
   - **Remote Cluster:** `http://localhost:6333` (production/Docker).
   - **Embedded On-Disk:** `./qdrant_local_store` (local developer serving).
   - **In-Memory Fallback:** `:memory:` (used during concurrent test runs or if disk locks are detected).
2. **Indexing:** Qdrant utilizes HNSW (Hierarchical Navigable Small World) graphs, offering logarithmic search time complexity $O(\log N)$ with high precision.
3. **Payload Storage:** Each vector point contains the original `page_content` and structured `metadata` (publisher, URL, topic, content hash).

---

## 5. Step 4: Retrieval & Reranker Pipeline

**Source Files:** [app/rag/query_builder.py](file:///home/pruthvi/projects/multiagentrag/app/rag/query_builder.py), [app/rag/retrieval_service.py](file:///home/pruthvi/projects/multiagentrag/app/rag/retrieval_service.py)

### Phase 1: Query Preparation (`prepare_retrieval_query`)
Rather than searching raw conversational chatter (e.g. *"yeah it started yesterday and it hurts a lot"*), `prepare_retrieval_query()` combines:
- Normalized primary symptom (e.g. *"headache"*).
- Active modifier attributes (e.g. *"throbbing, moderate, duration: 2 days"*).
- Associated symptoms (e.g. *"nausea"*).
- Formulates a targeted clinical query: `"throbbing headache duration 2 days nausea"`.

### Phase 2: First-Stage Dense Retrieval (Bi-Encoder)
```python
hits = client.search(
    collection_name="medical_triage_kb",
    query_vector=embed_query(dense_query),
    limit=settings.fetch_k,         # fetch_k = 20
    score_threshold=settings.score_threshold, # score_threshold = 0.55
    with_payload=True,
)
```
- Retrieves up to 20 candidate documents with a cosine similarity of at least 0.55.
- Deduplicates documents by `document_id`.

### Phase 3: Second-Stage Cross-Encoder Reranking
```python
reranker = get_reranker() # BAAI/bge-reranker-base
pairs = [(scoring_query, doc.page_content) for doc in candidates]
scores = reranker.predict(pairs)
ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
final_docs = [doc for doc, score in ranked[:settings.final_k]] # final_k = 5
```
- **Why Rerank?** Bi-encoders map query and document independently into fixed 384d vectors. The Cross-Encoder processes `[CLS] Query [SEP] Passage [SEP]` simultaneously through all transformer layers with full cross-attention. This catches nuanced medical qualifiers (e.g. distinguishing *"headache with aura"* from *"headache without aura"*).
- **Graceful Degradation:** If the reranker model throws an exception (e.g. OOM or timeout), `MedicalRetrievalService` catches it and returns the bi-encoder candidates directly with status `"reranker_degraded"`.

---

## 6. Step 5: Evidence Context Assembly & Synthesis

**Source Files:** [app/rag/context_builder.py](file:///home/pruthvi/projects/multiagentrag/app/rag/context_builder.py), [app/rag/synthesizer.py](file:///home/pruthvi/projects/multiagentrag/app/rag/synthesizer.py)

### Context Assembly (`assemble_medical_context`)
Formats retrieved documents into numbered evidence blocks with token budgets:
```text
[S1] MED-MIGRAINE-WITHOUT-AURA-02: Clinical Diagnosis and Management of Acute Migraine
Publisher: NICE Clinical Guidelines (CG150) | Topic: Neurology / Migraine
URL: https://www.nice.org.uk/guidance/cg150
Content: Migraine is a recurrent neurological disorder typically presenting with unilateral, throbbing...

[S2] MED-TENSION-HEADACHE-01: Tension-Type Headache Clinical Diagnosis & Home Care...
```

### Synthesis Prompt & Grounding Rules
`EvidenceGroundedSynthesizer` passes the assembled context and `PatientCase` into `ChatGroq` (`qwen/qwen3.6-27b`). The prompt enforces:
1. **Zero Hallucination:** You may ONLY cite facts explicitly contained in `[S1..S5]`.
2. **Explicit Citations:** Every candidate condition and home-care action MUST include `supporting_evidence_ids` (e.g. `["[MED-MIGRAINE-WITHOUT-AURA-02]"]`).
3. **Structured Pydantic Output:** Coerced into `GroundedAssessmentResponse`:
   - `case_summary`: Summary of reported symptoms.
   - `possible_conditions`: List of differential conditions with evidence justifications and findings against.
   - `recommended_actions`: Evidence-backed supportive care (hydration, rest).
   - `warning_signs`: Red flags requiring immediate clinical escalation.
   - `evidence_limitations`: What could not be confirmed without in-person tests.
   - `disclaimer`: Non-diagnostic triage decision-support notice.

---

## 7. Step 6: Citation Validation

**Source File:** [app/rag/citation_validator.py](file:///home/pruthvi/projects/multiagentrag/app/rag/citation_validator.py)

Even with strict prompt instructions, LLMs can fabricate source IDs. `CitationValidator` runs deterministic regex verification on generated output:
1. Extracts all tokens matching `\[(S\d+|Source\s*\d+)\]` and `\[(MED-[A-Z0-9\-]+)\]`.
2. Compares extracted tokens against the `available_sources` actually provided in the context.
3. If the LLM generates a hallucinated citation (e.g. `[MED-COVID-19-99]` when only Migraine and Tension Headache were retrieved), `CitationValidator` flags it in `unsupported_citations` and sets `is_valid=False`.

---

## 8. Step 7: Conversational State & Adaptive Questioning

**Source Files:** [app/services/patient_case.py](file:///home/pruthvi/projects/multiagentrag/app/services/patient_case.py), [app/services/question_planner.py](file:///home/pruthvi/projects/multiagentrag/app/services/question_planner.py), [app/services/patient_lookup.py](file:///home/pruthvi/projects/multiagentrag/app/services/patient_lookup.py)

1. **Structured Memory (`PatientCase`):**
   - Tracks `reported_symptoms` with status (`present`, `absent`, `unknown`), severity (1-10), duration, and onset.
   - Prevents context contamination: denied symptoms (e.g. *"no fever"*) are explicitly tagged as `absent`, ensuring differential diagnosis does not consider fever-related infections.
2. **Adaptive Questioning Loop:**
   - In `adaptive_intake_check_node`, if primary symptom, duration, or key red flags are missing, the system generates **one targeted follow-up question at a time** (e.g. *"How many days have you had this headache?"*).
   - **Anti-Repetition:** `PatientLookupEngine.check_greeting` and `case.question_history` ensure the user is never asked the same question twice.
   - **Turn Cap:** To prevent endless questioning loops, intake is strictly capped at `max_intake_turns=7`. If the turn limit is reached, the system transitions immediately to differential assessment.

---

## 9. Failure Scenarios & Graceful Degradation

| Failure Mode | Root Cause | System Response & Mitigation |
| :--- | :--- | :--- |
| **Emergency Red Flag** | User mentions chest pain, stroke, severe breathing difficulty | `SafetyEngine` intercepts input with zero LLM tokens, short-circuits graph, and outputs emergency ER numbers. |
| **Vector DB Unreachable** | Qdrant service offline or connection refused | `MedicalRetrievalService` catches exception, sets `status="vector_store_unavailable"`, and falls back to in-memory store or safe clinical fallback. |
| **No Documents Pass Threshold** | Rare or obscure symptom query scores < 0.55 | `RetrievalResult` returns `status="no_results"`. Synthesizer outputs honest statement of insufficient evidence and advises in-person evaluation. |
| **Cross-Encoder Failure / Timeout** | High CPU contention or PyTorch memory issue | Caught in `try...except`, returns top bi-encoder candidate documents with `status="reranker_degraded"`. |
| **LLM Rate Limit (HTTP 429)** | Groq quota exhausted on single API key | `get_llm()` implements round-robin cycling across `GROQ_API_KEYS` with 3 automatic retries. |
| **Prompt Injection** | Malicious user input attempts to override system prompt | `PatientLookupEngine` and `prepare_retrieval_query` sanitize inputs; synthesizer prompt isolates context in explicit XML/fenced boundaries. |
| **Hallucinated Citations** | LLM references non-existent guideline ID | `CitationValidator` flags unsupported tokens in audit log and strips invalid citations before delivery. |
