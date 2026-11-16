# Complete Technology Stack Analysis: BluCare+

This document breaks down every technology in the BluCare+ repository, tracing where each is imported and executed, why it was chosen over alternatives, and how to defend these choices in technical interviews.

---

## 1. Technology Status Overview

| Technology | Category | Status in Repository | Primary File & Component |
| :--- | :--- | :--- | :--- |
| **FastAPI** (v0.115.6) | Web Framework | **Actively Used** | [app/main.py](file:///home/pruthvi/projects/multiagentrag/app/main.py), [app/api/v1/router.py](file:///home/pruthvi/projects/multiagentrag/app/api/v1/router.py) |
| **Uvicorn** (v0.32.1) | ASGI Server | **Actively Used** | Runtime server running the asynchronous event loop |
| **LangGraph** (v0.2.62) | Orchestration | **Actively Used** | [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py) `compiled_triage_graph` |
| **LangChain Core** (v0.3.x) | LLM Framework | **Actively Used** | Prompts, messages (`HumanMessage`, `AIMessage`), Document abstractions |
| **ChatGroq** (v0.2.1) | LLM Provider | **Actively Used** | [app/core/llm.py](file:///home/pruthvi/projects/multiagentrag/app/core/llm.py) `get_llm()` |
| **Qdrant Client** (v1.12.1) | Vector Database | **Actively Used** | [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py) `get_qdrant_client()`, [app/rag/retrieval_service.py](file:///home/pruthvi/projects/multiagentrag/app/rag/retrieval_service.py) |
| **HuggingFace Embeddings** | Vector Embeddings | **Actively Used** | [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py) `BAAI/bge-small-en-v1.5` (384 dimensions) |
| **Sentence-Transformers** | Cross-Encoder Reranker | **Actively Used** | [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py) `CrossEncoder('BAAI/bge-reranker-base')` |
| **SQLAlchemy** (v2.x) | Relational ORM | **Actively Used** | [app/db/models.py](file:///home/pruthvi/projects/multiagentrag/app/db/models.py), [app/db/repository.py](file:///home/pruthvi/projects/multiagentrag/app/db/repository.py), [app/db/session.py](file:///home/pruthvi/projects/multiagentrag/app/db/session.py) |
| **SQLite (WAL mode)** | State Checkpointing | **Actively Used** | [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py) `SqliteSaver` (`checkpoints.sqlite`) |
| **Redis** | Semantic Cache | **Actively Used / Configurable** | [app/services/semantic_cache.py](file:///home/pruthvi/projects/multiagentrag/app/services/semantic_cache.py) (Enabled via `REDIS_CACHE_ENABLED`) |
| **Clerk Auth** (PyJWT / Cryptography) | Authentication | **Actively Used** | [app/core/auth.py](file:///home/pruthvi/projects/multiagentrag/app/core/auth.py) JWT verification, JWKS caching |
| **RAGAS** | RAG Evaluation | **Actively Used** | [evaluation/metrics.py](file:///home/pruthvi/projects/multiagentrag/evaluation/metrics.py), [evaluation/runner.py](file:///home/pruthvi/projects/multiagentrag/evaluation/runner.py) |
| **Langfuse / LangSmith** | Observability | **Actively Used / Configurable** | [app/core/langfuse_client.py](file:///home/pruthvi/projects/multiagentrag/app/core/langfuse_client.py) |
| **Selenium** (v4.21.0) | Web Scraping | **Actively Used** | [app/facilities/scraper.py](file:///home/pruthvi/projects/multiagentrag/app/facilities/scraper.py) Headless Chrome hospital scraping |
| **React 19 + Vite** | Frontend Client | **Actively Used** | `frontend/src/` (Multi-RAG chat, glassmorphic UI, Clerk SDK) |

---

## 2. In-Depth Component Breakdown

### 2.1 Backend Framework: FastAPI & Uvicorn
1. **What is it?** High-performance Python ASGI web framework built on Starlette and Pydantic.
2. **What problem does it solve?** Handles asynchronous HTTP requests, input validation, OpenAPI schema generation, and dependency injection.
3. **Why BluCare+ needs it:** Triage operations mix non-blocking I/O (LLM API calls, database queries) with CPU-bound tasks (embeddings, cross-encoder scoring). FastAPI's async/sync threadpool model (`anyio.to_thread.run_sync`) ensures the event loop is never blocked.
4. **Where it is used:** [app/main.py](file:///home/pruthvi/projects/multiagentrag/app/main.py#L55-L95), [app/api/v1/router.py](file:///home/pruthvi/projects/multiagentrag/app/api/v1/router.py).
5. **Alternative comparison:**
   - *FastAPI vs Flask:* Flask is synchronous WSGI by default; streaming responses and async background tasks require Gevent or Celery. FastAPI has native `asyncio`, automatic Pydantic request validation, and generated `/docs`.
6. **Trade-off & Disadvantage:** Python GIL remains active in multithreaded compute; heavy CPU tasks (like running PyTorch models directly in the worker) can starve the event loop if not offloaded to threadpools.

---

### 2.2 Orchestration: LangGraph vs Custom Python State Machine
1. **What is it?** Graph-based state machine library extending LangChain to support cyclic workflows, conditional branching, and checkpointed persistence.
2. **What problem does it solve?** Managing multi-turn clinical triage requires maintaining state (reported symptoms, denied symptoms, pending questions, intake turns) and branching conditionally based on red-flag emergencies, missing facts, or post-assessment actions.
3. **Why BluCare+ needs it:** [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py) builds an 11-node `StateGraph(WorkflowState)` with persistence via `SqliteSaver` in WAL mode.
4. **Why chosen over alternatives:**
   - *LangGraph vs Pure Custom Python:* A plain `while` loop or dictionary-based state machine lacks standardized checkpointing, time-travel debugging, unified Langfuse/LangSmith tracing callbacks, and clear declarative routing edges.
   - *LangGraph vs Standard LangChain Chains:* Legacy LangChain chains are directed acyclic graphs (DAGs). Clinical triage requires cyclical looping (asking clarifying questions turn by turn until sufficient information is gathered).
5. **Trade-off & Disadvantage:** Adds runtime overhead and dependency lock-in. Serialization of state dicts across nodes must strictly adhere to Pydantic/TypedDict schemas.

---

### 2.3 Vector Database: Qdrant vs Chroma vs FAISS vs Pinecone
1. **What is it?** High-performance vector similarity search engine written in Rust with rich payload filtering and HNSW indexing.
2. **What problem does it solve?** Storing document embeddings and executing sub-millisecond nearest-neighbor search with metadata constraints.
3. **Why BluCare+ needs it:** [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py#L26-L75) connects to Qdrant via remote URL (`localhost:6333`), local embedded on-disk storage (`qdrant_local_store`), or isolated `:memory:` fallback.
4. **Why chosen over alternatives:**
   - *Qdrant vs Chroma:* Chroma is popular for quick prototypes, but historically had concurrency and file-locking issues in multi-worker Python environments. Qdrant is battle-tested in Rust, supports payload-based Boolean filtering (e.g. `clinical_topic == 'Neurology'`), and provides both local embedded mode and remote cloud clustering.
   - *Qdrant vs FAISS:* FAISS is an in-memory C++ index, not a database. It has no native metadata persistence, CRUD updates, or client-server architecture.
   - *Qdrant vs Pinecone:* Pinecone is cloud-only, closed-source, and introduces per-query network latency and external vendor dependency.
5. **Trade-off & Disadvantage:** In local embedded mode, only one process can hold the file write-lock on disk at a time (which BluCare+ handles gracefully by detecting `.lock` and falling back to in-memory mode with auto-sync).

---

### 2.4 Embeddings: BAAI/bge-small-en-v1.5
1. **What is it?** 384-dimensional dense transformer embedding model developed by BAAI (Beijing Academy of Artificial Intelligence).
2. **What problem does it solve?** Converts clinical text into dense semantic vector representations.
3. **Why BluCare+ needs it:** Powers dense similarity search in Qdrant with cosine metric.
4. **Why chosen over alternatives:**
   - *BGE Small vs OpenAI `text-embedding-3-small`:* BGE runs locally on CPU with zero per-token API cost, zero network latency, and strict HIPAA/PII data privacy (patient symptoms never leave the application).
   - *BGE Small vs `all-MiniLM-L6-v2`:* BGE v1.5 consistently outperforms MiniLM on MTEB (Massive Text Embedding Benchmark) retrieval tasks while maintaining identical 384-dimension efficiency.
5. **Crucial Technical Nuance (Asymmetric Search):**
   - BGE is trained asymmetrically: queries must be prefixed with `settings.bge_query_instruction` (*"Represent this sentence for searching relevant passages: "*), while passages in the knowledge base are embedded without the prefix. BluCare+ implements this separation explicitly in [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py#L117-L126) and [app/rag/document_ingestion.py](file:///home/pruthvi/projects/multiagentrag/app/rag/document_ingestion.py#L221-L222).

---

### 2.5 Reranker: BAAI/bge-reranker-base (Cross-Encoder)
1. **What is it?** Cross-encoder model that scores a `(query, passage)` pair simultaneously using full self-attention across both texts.
2. **What problem does it solve?** Bi-encoders (vector embeddings) encode queries and passages separately, missing fine-grained token-to-token interactions. This results in false-positive top-K candidates that share common medical vocabulary but describe different etiologies.
3. **Why BluCare+ needs it:** In [app/rag/retrieval_service.py](file:///home/pruthvi/projects/multiagentrag/app/rag/retrieval_service.py#L85-L103), Qdrant retrieves 20 candidate documents (`fetch_k=20`). The cross-encoder rescores and reorders these candidates, returning only the top 5 (`final_k=5`) to the LLM prompt.
4. **Trade-off:**
   - Cross-encoders are computationally heavier than bi-encoders (~1-3 seconds on CPU for 20 pairs). BluCare+ includes a fallback: if the reranker fails or times out, the service degrades gracefully to returning dense candidates directly (`status="reranker_degraded"`).

---

### 2.6 LLM Provider: Groq & ChatGroq
1. **What is it?** Cloud inference provider utilizing custom LPUs (Language Processing Units) running open-weights models (`qwen/qwen3.6-27b`, `llama-3`).
2. **What problem does it solve?** Clinical triage requires real-time streaming and conversational latency (< 2 seconds). Traditional GPU cloud instances often suffer from queuing and high time-to-first-token (TTFT).
3. **Why BluCare+ needs it:** [app/core/llm.py](file:///home/pruthvi/projects/multiagentrag/app/core/llm.py) configures `ChatGroq` with round-robin multi-key cycling (`get_groq_keys()`) to prevent rate limits during user surges.
4. **Why chosen over alternatives:**
   - *Groq vs Direct OpenAI GPT-4o:* Groq offers 300-500 tokens/sec generation speeds at significantly lower cost. For evidence-grounded RAG, where the clinical knowledge is supplied in context rather than relying on model parametric memory, an open 27B-70B model with strict prompt constraints matches GPT-4o accuracy while delivering a vastly superior user experience.
5. **Trade-off:** Groq's cloud hosts open models whose prompt formatting, system role adherence, and structured JSON parsing require defensive handling. BluCare+ uses Pydantic field validators and coercion in [app/rag/synthesizer.py](file:///home/pruthvi/projects/multiagentrag/app/rag/synthesizer.py) to prevent JSON schema parse errors.

---

### 2.7 Relational Database: PostgreSQL & SQLite via SQLAlchemy
1. **What is it?** Relational ORM mapping Python classes to SQL tables.
2. **What problem does it solve?** Persisting structured user sessions (`TriageSession`), turn history (`TriageMessage`), safety audit events (`TriageSafetyEvent`), and clinical assessments (`TriageAssessment`).
3. **Why chosen over NoSQL (e.g. MongoDB):**
   - Clinical audit trails require strict ACID guarantees and foreign key constraints (e.g. `ondelete="CASCADE"` from session to messages and safety events). A relational schema with composite indexes (`ix_triage_sessions_user_status`) ensures multi-tenant isolation by user ID.

---

### 2.8 Evaluation: RAGAS
1. **What is it?** Automated evaluation framework for Retrieval-Augmented Generation systems.
2. **What problem does it solve?** Validates RAG quality across 4 mathematical metrics:
   - **Faithfulness:** Are all generated claims grounded in the retrieved context?
   - **Answer Relevancy:** Does the generated response directly answer the user's specific symptom?
   - **Context Precision:** Are relevant passages ranked higher than irrelevant ones?
   - **Context Recall:** Did retrieval fetch all facts needed to answer the ground truth?
3. **Where it is used:** [evaluation/metrics.py](file:///home/pruthvi/projects/multiagentrag/evaluation/metrics.py), with regression benchmarks in [RAGAS_BASELINE_REPORT.md](file:///home/pruthvi/projects/multiagentrag/RAGAS_BASELINE_REPORT.md).

---

## 3. Technology Stack Interview Summary (What to Speak in an Interview)

> *"In BluCare+, I architected a modern, production-grade conversational RAG backend using **FastAPI** and **LangGraph** in Python. For retrieval, I chose a two-stage hybrid pipeline: first, **Qdrant** executes dense vector search using **BAAI/bge-small-en-v1.5** embeddings (384 dimensions) with asymmetric query prefixing; second, a **bge-reranker-base CrossEncoder** scores the top 20 candidate passages to eliminate lexical false positives and surface the top 5 most clinically relevant chunks.*
>
> *For synthesis, I orchestrated **ChatGroq** running **Qwen 27B** with round-robin API key distribution for sub-second inference speeds. Before any LLM call is made, an independent, zero-token **SafetyEngine** intercepts the input to detect emergency red flags like chest pain or stroke symptoms. Clinical state is tracked turn-by-turn using a custom `PatientCase` data model checkpointed via **SQLite WAL** in LangGraph and persisted in **PostgreSQL** via **SQLAlchemy**. Finally, the entire pipeline is verified using **RAGAS** automated metrics and traced end-to-end with **Langfuse**."*
