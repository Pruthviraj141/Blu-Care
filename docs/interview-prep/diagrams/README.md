# BluCare+ System Architecture & Flow Diagrams

This directory indexes the interactive, code-backed HTML architecture diagrams generated for BluCare+. Each diagram is standalone, explorable, and directly backed by evidence from the repository source code.

---

## 1. Complete System Architecture
- **Artifact:** [01-system-architecture.html](file:///home/pruthvi/projects/multiagentrag/.archify/01-system-architecture.html)
- **JSON Source:** [.archify/01-system-architecture.json](file:///home/pruthvi/projects/multiagentrag/.archify/01-system-architecture.json)
- **Type:** Architecture Diagram
- **What to Learn for Interviews:**
  - Understand the holistic topology: how the **React 19 Frontend** (Clerk-authenticated) connects to the **FastAPI Gateway** (`app/main.py`), which coordinates requests through **SessionService** (`app/core/session_service.py`).
  - Learn how the **SafetyEngine** (`app/services/safety_engine.py`) acts as a zero-token red-flag firewall before any LLM execution.
  - See how the **LangGraph 11-node StateGraph** (`app/graph/build_graph.py`) interacts with **Qdrant Vector DB** (`app/rag/store.py`), the local CPU-based **CrossEncoder Reranker**, and **ChatGroq** LLM API.
  - Observe data persistence in PostgreSQL/SQLite (`app/db/models.py`) and optional caching via Redis (`app/services/semantic_cache.py`).

---

## 2. Complete User Request Lifecycle
- **Artifact:** [02-request-lifecycle.html](file:///home/pruthvi/projects/multiagentrag/.archify/02-request-lifecycle.html)
- **JSON Source:** [.archify/02-request-lifecycle.json](file:///home/pruthvi/projects/multiagentrag/.archify/02-request-lifecycle.json)
- **Type:** Sequence Diagram
- **What to Learn for Interviews:**
  - Follow the exact chronological message path when a patient submits a message like *"throbbing headache for 2 days"*.
  - Step 1: Ingress via `POST /api/v1/session/message`, token validation via Clerk JWT middleware.
  - Step 2: SafetyEngine checks 5 provisional emergency rules (chest pain, stroke, breathing difficulty, anaphylaxis, thunderclap headache).
  - Step 3: State compilation and invocation into LangGraph `compiled_triage_graph`.
  - Step 4: Medical query preparation, dense cosine search in Qdrant (`fetch_k=20`), reranking down to `final_k=5`.
  - Step 5: Evidence-grounded synthesis with Pydantic JSON coercion, citation validation, database persistence, and HTTP 200 JSON return.

---

## 3. Conversational Follow-up Flow & Adaptive Intake
- **Artifact:** [03-conversational-flow.html](file:///home/pruthvi/projects/multiagentrag/.archify/03-conversational-flow.html)
- **JSON Source:** [.archify/03-conversational-flow.json](file:///home/pruthvi/projects/multiagentrag/.archify/03-conversational-flow.json)
- **Type:** Workflow Diagram
- **What to Learn for Interviews:**
  - How state is preserved across turns using `PatientCase` (`app/services/patient_case.py`) and SQLite checkpointing (`checkpoints.sqlite` with WAL mode).
  - How `PatientLookupEngine` performs deterministic symptom and duration extraction to prevent duplicate questions and hallucinated facts.
  - The branching logic in `adaptive_intake_check_node`:
    - If required clinical facts (primary symptom, duration, severity) are incomplete and turn < 7 -> branch to `ask_one_question_node`.
    - Once required information is present or max 7 turns reached -> branch to `retrieve_medical_evidence_node` and full differential synthesis.

---

## 4. Medical RAG Pipeline & Dataflow Topology
- **Artifact:** [04-rag-dataflow.html](file:///home/pruthvi/projects/multiagentrag/.archify/04-rag-dataflow.html)
- **JSON Source:** [.archify/04-rag-dataflow.json](file:///home/pruthvi/projects/multiagentrag/.archify/04-rag-dataflow.json)
- **Type:** Dataflow Diagram
- **What to Learn for Interviews:**
  - **Ingestion Pipeline:** How curated WHO, NICE, and CDC clinical guidelines are loaded, hashed (SHA-256), and embedded into Qdrant (`medical_triage_kb` collection) using pure passage embeddings (WITHOUT prefix) at 384 dimensions.
  - **Query & Retrieval Pipeline:** How incoming user queries are formulated by `prepare_retrieval_query()`, prefixed with BGE's asymmetric query instruction (`"Represent this sentence for searching relevant passages: "`), and executed against Qdrant with a cosine score threshold of 0.55.
  - **Reranker Stage:** How the top-20 candidates are reranked on CPU using `BAAI/bge-reranker-base` CrossEncoder to filter out superficial lexical matches.
  - **Synthesis & Verification:** How `AssembledEvidenceContext` structures the evidence with `[S1..S5]` tokens, and `CitationValidator` detects any unsupported or hallucinated citation tokens.
