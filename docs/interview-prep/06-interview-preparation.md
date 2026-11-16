# Complete Technical Interview Preparation Guide: BluCare+

This document is your master interview preparation manual. It prepares you to present, explain, justify, debug, and defend the BluCare+ Medical AI Triage and RAG project in technical interviews.

---

## Table of Contents
1. [A. Project Introductions (30s, 1m, 2m)](#a-project-introductions)
2. [B. System Architecture Explanation](#b-system-architecture-explanation)
3. [C. Technology Justifications](#c-technology-justifications)
4. [D. Deep RAG Technical Questions & Answers](#d-deep-rag-technical-questions--answers)
5. [E. Backend, Database & Concurrency Questions](#e-backend-database--concurrency-questions)
6. [F. System Design & Scalability Scenarios (10x Traffic)](#f-system-design--scalability-scenarios)
7. [G. Code-Level Deep Dives (Core Functions)](#g-code-level-deep-dives)
8. [H. Project Limitations & Honest Weaknesses](#h-project-limitations--honest-weaknesses)
9. [I. Top 25 Technical Interview Questions & Model Answers](#i-top-25-technical-interview-questions--model-answers)
10. [J. Quick Revision Sheet (Two-Page Summary)](#j-quick-revision-sheet)

---

## A. Project Introductions

### 1. The 30-Second Elevator Pitch
> *"BluCare+ is an AI-powered conversational medical symptom triage and RAG application. It guides patients through an adaptive clinical dialogue to collect reported symptoms, durations, and severities, screens for emergency red flags with zero LLM tokens, and retrieves verified clinical guidelines from WHO, NICE, and CDC. Using a two-stage retrieve-and-rerank pipeline with Qdrant and a CrossEncoder, it synthesizes an evidence-grounded differential assessment with verified citations, followed by real-time GPS-based clinic discovery."*

### 2. The 1-Minute Project Overview
> *"During my final year in AI and Data Science engineering, I noticed that generic LLMs frequently hallucinate or give unsafe medical advice when asked health questions. To solve this, I designed BluCare+.*
>
> *BluCare+ is an agentic clinical triage system built with FastAPI and LangGraph. When a user describes a symptom, the system first passes the text through a deterministic `SafetyEngine` that scans for emergency red flags like stroke or chest pain without consuming LLM tokens. If safe, an adaptive intake state machine collects missing clinical facts over a maximum of 7 turns.*
>
> *Once the clinical picture is complete, BluCare+ uses an asymmetric embedding model (`bge-small-en-v1.5`) in Qdrant to retrieve candidate clinical guidelines, reranks them using a CrossEncoder (`bge-reranker-base`), and prompts a Groq-hosted open LLM to generate differential possibilities, warning signs, and supportive care. Finally, a regex citation validator confirms that all cited document IDs actually exist in the retrieved context. The entire pipeline is verified using automated RAGAS metrics."*

### 3. The 2-Minute Deep Technical Explanation
> *"BluCare+ is an end-to-end medical triage and RAG platform addressing three core challenges in health AI: diagnostic hallucinations, emergency safety, and contextual clinical dialogue.*
>
> *On the frontend, patients interact through a responsive React 19 application secured with Clerk JWT authentication. The backend is an asynchronous FastAPI service structured into clean operational layers.*
>
> *The conversation lifecycle is orchestrated by an 11-node LangGraph state machine with SQLite WAL checkpointing. When a request arrives at `/api/v1/session/message`, the system loads the patient's cumulative case state. Before any AI reasoning occurs, the `SafetyEngine` executes a zero-token regex evaluation of five critical red-flag rules. If an emergency is triggered, execution short-circuits immediately to provide emergency telephone directories.*
>
> *For non-emergency inputs, the intake engine extracts symptoms and modifiers, updating a structured `PatientCase` model. If key attributes like duration or severity are missing, an adaptive question planner asks targeted follow-up questions.*
>
> *When sufficient information is collected, the workflow enters a two-stage RAG pipeline. Stage 1 searches a Qdrant vector collection using 384-dimensional BGE Small embeddings with cosine similarity to retrieve the top 20 candidates. Stage 2 passes these candidates into a CPU-based CrossEncoder reranker to eliminate superficial lexical matches, passing the top 5 documents to ChatGroq. The LLM generates a structured differential assessment constrained by Pydantic validators. A deterministic `CitationValidator` audits the output tokens, and the finalized assessment is persisted in PostgreSQL.*
>
> *To measure system quality, I benchmarked the pipeline using RAGAS, achieving 0.95 Faithfulness, 0.90 Answer Relevancy, and 1.0 Context Precision."*

---

## B. System Architecture Explanation

### Request Flow Walkthrough
1. **Ingress:** Patient sends `"throbbing headache for 2 days"` via React frontend.
2. **Auth Verification:** FastAPI middleware verifies Clerk JWT Bearer token and extracts `user_id`.
3. **Session Coordination:** `SessionService` checks session ownership in PostgreSQL.
4. **Safety Screening:** `SafetyEngine.evaluate()` scans text against emergency rules. Outcome: safe.
5. **State Restoration:** LangGraph loads `PatientCase` from SQLite checkpointer.
6. **Symptom Extraction:** `PatientLookupEngine` and `SymptomExtractor` normalize `headache` (present), `throbbing` (attribute), `duration` (2 days).
7. **Adaptive Decision:** `adaptive_intake_check_node` verifies required facts. Since primary symptom and duration are present, it transitions to RAG.
8. **Dense Retrieval:** `MedicalRetrievalService` prefixes query with BGE search instruction and retrieves top-20 chunks from Qdrant.
9. **CrossEncoder Rerank:** `bge-reranker-base` scores query-passage pairs, selecting top-5 chunks.
10. **Evidence Context:** `ContextBuilder` wraps chunks as `[S1..S5]` within token budget.
11. **Grounded Synthesis:** `ChatGroq` (`qwen/qwen3.6-27b`) synthesizes differential assessment JSON.
12. **Citation Validation:** `CitationValidator` confirms all `[MED-xxx]` tokens match retrieved sources.
13. **Persistence:** `TriageRepository` saves `TriageAssessment` and updates session turn in PostgreSQL.
14. **Frontend Delivery:** HTTP 200 returned with assessment summary, sources, and interactive action buttons (e.g. *Find Nearby Clinics*, *Ayurvedic Guidance*).

---

## C. Technology Justifications

### 1. Why Python and FastAPI?
- **Python:** Standard language for AI/ML, offering native support for PyTorch, HuggingFace, LangChain, and RAGAS.
- **FastAPI:** Built on Starlette with asynchronous event-loop architecture. Handles concurrent I/O (database, external LLM calls) while offloading CPU-heavy transformer scoring to threadpools via `anyio.to_thread.run_sync`. Provides automatic Pydantic request validation and interactive OpenAPI `/docs`.

### 2. Why LangGraph Instead of Standard LangChain Chains?
- Standard LangChain chains are directed acyclic graphs (DAGs). Clinical triage requires **cyclical loops**: asking follow-up questions, updating memory, evaluating completion, and looping back until sufficient information is gathered. LangGraph provides native cyclic state machines with built-in checkpointing (`SqliteSaver`).

### 3. Why Qdrant Vector Database?
- High-performance Rust vector engine with sub-millisecond HNSW indexing.
- Provides native payload-based metadata filtering (e.g. filtering guidelines by `clinical_topic`).
- Offers both local embedded mode (for self-contained edge execution) and distributed client-server mode.

### 4. Why BAAI/bge-small-en-v1.5 Embeddings?
- Runs locally on CPU with zero per-token API cost and zero external latency.
- Keeps patient medical data private on-premises (HIPAA/GDPR compliance).
- Outperforms MiniLM on MTEB benchmarks while generating compact 384-dimensional vectors.

### 5. Why a Two-Stage Retrieve-and-Rerank Pipeline?
- Bi-encoders encode queries and documents into independent vector vectors. They are fast ($O(1)$ lookup via HNSW) but lack token-to-token cross-attention, causing false-positive lexical matches.
- A CrossEncoder reranker scores `(query, passage)` pairs jointly with full self-attention, significantly boosting Context Precision by placing the most clinically accurate guideline at rank 1.

### 6. Why ChatGroq with Qwen 27B / Llama 3?
- Groq's LPU architecture delivers generation speeds of 300–500 tokens/second.
- Open-weights models (27B/70B) constrained by evidence context match proprietary models (GPT-4o) in accuracy while reducing cost by over 80%.

---

## D. Deep RAG Technical Questions & Answers

### Q1: What is the difference between dense retrieval and sparse retrieval?
- **Answer:** Sparse retrieval (e.g. BM25 / TF-IDF) relies on exact lexical keyword matching. It fails when users express symptoms with synonyms (e.g. *"tummy ache"* vs *"gastroenteritis"*). Dense retrieval uses neural bi-encoder embeddings to map phrases into a continuous latent space where semantic similarity corresponds to vector cosine proximity.

### Q2: What is asymmetric embedding, and why is it critical in BluCare+?
- **Answer:** In asymmetric search, the search query (short, interrogative) has a different linguistic structure than the stored passage (detailed, declarative clinical guideline). Models like BGE are trained to bridge this gap by requiring a specific instruction prefix on queries (`"Represent this sentence for searching relevant passages: "`), while passages are ingested without the prefix. Omitting or swapping this prefix degrades retrieval recall.

### Q3: How do you prevent LLM hallucinations in medical RAG?
- **Answer:** Through a five-layer defense:
  1. **Strict Context Boundaries:** System prompt explicitly instructs the LLM that facts outside `[S1..S5]` do not exist.
  2. **Low Temperature:** Set to `0.2` to minimize sampling randomness.
  3. **Pydantic Schema Validation:** Structured output schema requires explicit `supporting_evidence_ids` for every differential condition.
  4. **CitationValidator:** Deterministic regex scans the output for fabricated source tokens.
  5. **Negative Constraint:** If retrieved documents do not cover the symptom, the model must declare `is_insufficient_evidence: True` rather than guessing.

### Q4: What is Context Precision and Context Recall in RAGAS?
- **Context Precision:** Measures whether all relevant chunks in the retrieved context are ranked at the top. High precision means the LLM reads the best evidence first.
- **Context Recall:** Measures whether the retrieved context contains all the necessary facts to answer the ground-truth clinical question.

---

## E. Backend, Database & Concurrency Questions

### Q1: How does BluCare+ maintain session state between HTTP turns?
- **Answer:** State is maintained via a composite strategy:
  1. `TriageSession` table in PostgreSQL stores `case_state` (JSON) and `pending_question`.
  2. `TriageMessage` records each user and assistant turn with an incremental `turn_id`.
  3. LangGraph checkpoints the graph execution state in `checkpoints.sqlite` using `thread_id`. When a message arrives, `SessionService` loads the existing state, merges newly reported symptoms, and passes the updated state into the graph.

### Q2: How do you handle concurrency when multiple users access the API?
- **Answer:** FastAPI runs on the Uvicorn ASGI event loop. Non-blocking asynchronous I/O (network requests, database calls) runs cooperatively. CPU-bound operations (transformer embeddings and CrossEncoder scoring) are dispatched to worker threadpools using `anyio.to_thread.run_sync()`. This guarantees that heavy model inference never blocks Uvicorn from accepting incoming connections.

---

## F. System Design & Scalability Scenarios

### Scenario 1: What happens if traffic increases 10x?
1. **Bottleneck:** Local CPU-bound CrossEncoder reranking will saturate CPU cores, causing request queuing.
2. **Mitigation:**
   - **Step 1:** Enable the Redis Semantic Cache (`settings.redis_cache_enabled = True`). Common educational queries (e.g. *"What are tension headache symptoms?"*) return in < 5ms without invoking Qdrant or the CrossEncoder.
   - **Step 2:** Scale Uvicorn across multiple processes using Gunicorn process manager (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker`).
   - **Step 3:** Decouple embedding and reranking into dedicated containerized endpoints (e.g. HuggingFace TEI).

### Scenario 2: What happens if the Groq LLM API goes down?
1. **System Response:** `get_llm()` is configured with `max_retries=3` and round-robin multi-key failover.
2. **Graceful Fallback:** If all Groq keys fail, the exception handler catches `HTTPException(500)` and returns a structured message advising the patient that clinical synthesis is temporarily degraded and providing direct contact numbers for primary care facilities.

---

## G. Code-Level Deep Dives

### Function 1: `SafetyEngine.evaluate()`
- **File:** [app/services/safety_engine.py](file:///home/pruthvi/projects/multiagentrag/app/services/safety_engine.py#L61-L101)
- **Input:** `user_message: str`, optional `primary_symptom`, `associated_symptoms`.
- **Output:** `SafetyEvaluationResult` (`is_emergency: bool`, `rule_id`, `emergency_message`).
- **Logic:** Normalizes text and executes substring matching against verified critical keyword patterns (e.g. `"chest pain"`, `"facial drooping"`, `"slurred speech"`, `"throat closing"`).
- **Why it matters:** Zero LLM token cost, deterministic execution (< 1ms), and immune to prompt injection attacks.

### Function 2: `MedicalRetrievalService.retrieve()`
- **File:** [app/rag/retrieval_service.py](file:///home/pruthvi/projects/multiagentrag/app/rag/retrieval_service.py#L25-L113)
- **Input:** `dense_query: str`, optional `limit`, `use_reranker`.
- **Output:** `RetrievalResult` (list of `Document`, status, `reranker_applied`).
- **Logic:**
  1. Computes dense vector with `embed_query()` (prefixed).
  2. Queries Qdrant collection with `score_threshold=0.55` and `fetch_k=20`.
  3. Passes candidate pairs to `CrossEncoder.predict()`.
  4. Sorts by rerank score and slices top `final_k=5`.
  5. Includes `try...except` block falling back to dense candidates if reranker encounters an error.

### Function 3: `CitationValidator.validate()`
- **File:** [app/rag/citation_validator.py](file:///home/pruthvi/projects/multiagentrag/app/rag/citation_validator.py#L22-L91)
- **Input:** `text: str`, `available_sources: List[Dict[str, Any]]`.
- **Output:** `CitationValidationResult` (`is_valid`, `referenced_sources`, `unsupported_citations`, `claims_grounded`).
- **Logic:** Extracts citation tokens like `[S1]` and canonical IDs like `[MED-TENSION-HEADACHE-01]` via regex, maps them against verified source keys, and flags any hallucinated citation tokens.

---

## H. Project Limitations & Honest Weaknesses

When asked about limitations, present these real engineering trade-offs:
1. **CPU Reranker Latency:** `bge-reranker-base` on CPU adds ~1.5s to response time. In version 2, I would optimize this using FP16 quantization or ONNX Runtime.
2. **Curated Knowledge Base Size:** The current knowledge base contains verified clinical guidelines for primary care conditions (headache, respiratory, gastrointestinal, dengue). In production, this would expand to a medical knowledge graph covering thousands of ICD-10 conditions.
3. **Selenium Scraping Overhead:** Real-time facility discovery uses headless Chrome, which is resource-intensive. Transitioning to a pre-indexed geospatial PostGIS database with OpenStreetMap points would reduce facility search latency from 3s to 20ms.

---

## I. Top 25 Technical Interview Questions & Model Answers

### Question 1: What is BluCare+ and what problem does it solve?
- **Answer:** BluCare+ is an AI clinical triage and RAG application that provides evidence-grounded differential symptom assessments. It solves the critical problem of medical LLM hallucinations and safety risks by combining zero-token emergency red-flag screening, an adaptive conversational intake state machine, two-stage vector retrieval, and deterministic citation validation.
- **BluCare+ Example:** [app/main.py](file:///home/pruthvi/projects/multiagentrag/app/main.py), [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py).
- **Follow-up:** *How do you prevent patients from mistaking it for a doctor?* Every response includes a prominent clinical disclaimer stating BluCare+ is a non-diagnostic decision-support tool.

### Question 2: Why did you choose LangGraph over a custom Python state machine?
- **Answer:** LangGraph provides native support for cyclical agent workflows, built-in state checkpointing with SQLite WAL persistence, fine-grained conditional routing edges, and first-class observability tracing with Langfuse and LangSmith.
- **BluCare+ Example:** [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py) compiles `StateGraph(WorkflowState)`.
- **Follow-up:** *What happens if the server crashes mid-session?* The SQLite checkpointer restores the session state at the exact node where it left off using `thread_id`.

### Question 3: What is the benefit of a two-stage retrieve-and-rerank architecture?
- **Answer:** First-stage dense retrieval (bi-encoder) rapidly scans millions of vectors using HNSW to fetch candidates with low latency ($O(\log N)$). Second-stage CrossEncoder reranking applies full cross-attention across the query and candidate passages, catching subtle linguistic context that bi-encoders miss.
- **BluCare+ Example:** [app/rag/retrieval_service.py](file:///home/pruthvi/projects/multiagentrag/app/rag/retrieval_service.py) fetches 20 candidates and reranks to top 5.
- **Follow-up:** *Why not use CrossEncoder for the entire database?* CrossEncoders require $O(N)$ transformer forward passes; running it across thousands of documents would take minutes per query.

### Question 4: How does BluCare+ screen for medical emergencies?
- **Answer:** Using a deterministic `SafetyEngine` that scans for emergency red-flag keywords before calling the LLM. If chest pain or stroke symptoms are detected, the system exits the graph immediately, providing emergency telephone numbers (911, 999, 112).
- **BluCare+ Example:** [app/services/safety_engine.py](file:///home/pruthvi/projects/multiagentrag/app/services/safety_engine.py).
- **Follow-up:** *Why not use an LLM for safety classification?* LLMs can hallucinate, suffer from latency, and be bypassed by prompt injection. Rule-based evaluation is deterministic, zero-cost, and instant.

### Question 5: What is asymmetric embedding in BGE models?
- **Answer:** BGE models require search queries to be prefixed with a task prompt (`"Represent this sentence for searching relevant passages: "`), whereas documents in the corpus are embedded as raw passages.
- **BluCare+ Example:** [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py#L117-L126).
- **Follow-up:** *What happens if you omit the prefix?* Retrieval recall drops significantly because queries and passages are projected into divergent vector distributions.

### Question 6: How do you prevent context contamination during multi-turn triage?
- **Answer:** The `PatientCase` model records symptoms with structured status (`present`, `absent`, `unknown`). When a user denies a symptom (e.g. *"no fever"*), it is stored as `absent`, preventing the RAG pipeline from retrieving febrile illness guidelines.
- **BluCare+ Example:** [app/services/patient_case.py](file:///home/pruthvi/projects/multiagentrag/app/services/patient_case.py).
- **Follow-up:** *How do you prevent the bot from asking the same question twice?* `PatientLookupEngine` tracks `question_history` on the case.

### Question 7: How does CitationValidator work?
- **Answer:** It extracts `[S1..S5]` and canonical `[MED-xxx]` tokens from generated text using regex, matches them against the retrieved evidence IDs, and flags any hallucinated citations.
- **BluCare+ Example:** [app/rag/citation_validator.py](file:///home/pruthvi/projects/multiagentrag/app/rag/citation_validator.py).
- **Follow-up:** *What do you do when an invalid citation is detected?* The system logs a warning, flags `is_valid=False`, and strips the unsupported token.

### Question 8: Why Qdrant over Chroma or FAISS?
- **Answer:** Qdrant is built in Rust with high concurrency, native payload filtering, and flexible deployment options (embedded on-disk or distributed cluster). Chroma has had multi-worker lock issues, and FAISS lacks built-in document metadata management.
- **BluCare+ Example:** [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py).

### Question 9: What is the purpose of RAGAS in your project?
- **Answer:** RAGAS automates evaluation of RAG systems without human labeling by measuring Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
- **BluCare+ Example:** [evaluation/metrics.py](file:///home/pruthvi/projects/multiagentrag/evaluation/metrics.py).
- **Follow-up:** *What scores did you achieve?* 0.95 Faithfulness, 0.90 Answer Relevancy, and 1.0 Context Precision.

### Question 10: How do you handle database connection pooling in FastAPI?
- **Answer:** SQLAlchemy `engine` manages a connection pool. In production, we configure `pool_size=20`, `max_overflow=10`, and `pool_pre_ping=True` to prevent stale connections.
- **BluCare+ Example:** [app/db/session.py](file:///home/pruthvi/projects/multiagentrag/app/db/session.py).

### Question 11: How do you prevent prompt injection?
- **Answer:** User input is never injected directly into raw template strings. Prompts use structured `SystemMessage` and `HumanMessage` schemas with explicit XML tags separating instructions from user data.

### Question 12: Why did you cap intake at 7 turns?
- **Answer:** To prevent patient frustration and dialogue loops. If required facts are not gathered in 7 turns, the system proceeds with available data and highlights clinical uncertainties.

### Question 13: How does the Redis Semantic Cache work?
- **Answer:** It embeds educational inquiries and queries Redis for cached answers within a vector distance threshold (< 0.08). Hits return in < 5ms without LLM calls.
- **BluCare+ Example:** [app/services/semantic_cache.py](file:///home/pruthvi/projects/multiagentrag/app/services/semantic_cache.py).

### Question 14: How does Clerk authentication integrate with FastAPI?
- **Answer:** The frontend sends a JWT in the `Authorization: Bearer <token>` header. FastAPI middleware verifies the signature against Clerk's public JWKS endpoint.
- **BluCare+ Example:** [app/core/auth.py](file:///home/pruthvi/projects/multiagentrag/app/core/auth.py).

### Question 15: How does FacilitiesService discover nearby hospitals?
- **Answer:** It takes validated user GPS coordinates, maps differential conditions to medical specialties (e.g. Cardiology), and uses headless Chrome to scrape verified local clinics with Haversine distance calculations.
- **BluCare+ Example:** [app/facilities/service.py](file:///home/pruthvi/projects/multiagentrag/app/facilities/service.py).

### Question 16: What is Haversine distance?
- **Answer:** An equation giving great-circle distances between two points on a sphere from their longitudes and latitudes.
- **BluCare+ Example:** [app/facilities/distance.py](file:///home/pruthvi/projects/multiagentrag/app/facilities/distance.py).

### Question 17: How is Groq API quota managed across requests?
- **Answer:** `get_llm()` implements round-robin key cycling across comma-separated keys in `GROQ_API_KEYS` with automatic retries.
- **BluCare+ Example:** [app/core/llm.py](file:///home/pruthvi/projects/multiagentrag/app/core/llm.py).

### Question 18: What is cosine similarity in vector search?
- **Answer:** The cosine of the angle between two non-zero vectors: $\cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|}$. It measures semantic directional alignment regardless of magnitude.

### Question 19: Why normalize embeddings during ingestion?
- **Answer:** When vectors have unit length ($\|A\|=1$), cosine similarity simplifies to dot product $A \cdot B$, speeding up nearest-neighbor calculations.

### Question 20: How do you ensure multi-tenant user isolation?
- **Answer:** `TriageSession` stores `clerk_user_id`. `SessionService.process_message()` compares the authenticated token's user ID with the session record; mismatches return HTTP 403 Forbidden.

### Question 21: What is graceful degradation in BluCare+?
- **Answer:** If the CrossEncoder fails, the system returns dense candidates (`status="reranker_degraded"`). If remote Qdrant is unavailable, it falls back to local embedded or in-memory storage.

### Question 22: What is the role of `ContextBuilder`?
- **Answer:** It formats retrieved documents into structured evidence blocks with source tokens `[S1..S5]`, clinical topic headers, and URLs, while enforcing token budget limits.

### Question 23: How do you evaluate clinical faithfulness?
- **Answer:** RAGAS extracts factual statements from the generated response and uses an evaluator LLM to verify whether each statement is mathematically entailed by the retrieved context.

### Question 24: What is the difference between synchronous and asynchronous endpoints in FastAPI?
- **Answer:** `async def` runs directly on the asyncio event loop (ideal for non-blocking I/O). `def` runs in an external threadpool to prevent blocking the event loop with synchronous work.

### Question 25: What is your primary takeaway from building BluCare+?
- **Answer:** Building production AI is 20% model prompting and 80% systems engineering: deterministic safety rules, robust retrieval pipelines, schema enforcement, citation verification, and automated evaluation metrics.

---

## J. Quick Revision Sheet (Two-Page Summary)

### Architecture in One Glance
- **Frontend:** React 19 + Tailwind CSS + Clerk Auth.
- **API Gateway:** FastAPI + Correlation ID + Security Headers.
- **Safety:** Zero-Token Deterministic Rule-Based `SafetyEngine`.
- **Workflow:** LangGraph 11-node StateGraph + SQLite WAL checkpointer.
- **Stage 1 Retrieval:** Qdrant (HNSW, Cosine) + `BAAI/bge-small-en-v1.5` (384d, asymmetric query prefix).
- **Stage 2 Reranking:** `BAAI/bge-reranker-base` CrossEncoder on CPU (Top-20 -> Top-5).
- **Synthesis:** ChatGroq (`qwen/qwen3.6-27b`) with Pydantic JSON coercion.
- **Verification:** `CitationValidator` regex audit on `[MED-xxx]` tokens.
- **Storage:** PostgreSQL (Sessions, Messages, Assessments) + Redis (Semantic Cache).

### Key Metrics to Quote
- **Faithfulness:** 0.95 (Claims grounded in context).
- **Answer Relevancy:** 0.90 (Directness to user symptoms).
- **Context Precision:** 1.0 (Top-ranked evidence accuracy).
- **Embedding Dimensions:** 384 dimensions.
- **Score Threshold:** 0.55 cutoff in Qdrant.
- **Max Intake Turns:** 7 turns before forced differential assessment.
- **P99 Response Time:** ~1.8 seconds (dominated by CPU reranker).
