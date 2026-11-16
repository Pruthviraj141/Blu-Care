# Codebase Architecture Review: BluCare+

This architectural review analyzes the module boundaries, coupling, and complexity of BluCare+ using the principles of **improve-codebase-architecture**. It is designed to help you explain architectural trade-offs pragmatically in a system design interview.

---

## 1. Architectural Overview & Responsibility Analysis

BluCare+ is structured as a modular FastAPI backend with LangGraph workflow orchestration:

```
app/
├── api/             # HTTP ingress, routing, route handlers
│   └── v1/
│       └── endpoints/  # session, hospitals, assessments, user, upload
├── core/            # Cross-cutting concerns (config, auth, logging, llm, session_service)
├── graph/           # LangGraph workflow definition & node handlers
├── rag/             # Vector store, embeddings, retrieval, synthesis, citation validation
├── db/              # SQLAlchemy models, session factory, repository operations
├── services/        # Domain business logic (SafetyEngine, PatientCase, SymptomExtractor)
└── facilities/      # Scraping-based geolocation facility discovery
```

---

## 2. Key Architectural Issues & Refactoring Trade-offs

### Issue 1: Monolithic Graph Definition File (`app/graph/build_graph.py`)
- **Current Structure:**
  [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py) contains 1,167 lines of code, defining all 11 node implementations, state definitions, Pydantic type adapters, formatting helpers, and graph compilation in a single file.
  At the same time, individual files like `intake.py`, `retrieval.py`, `synthesis.py`, and `remedy.py` exist in the same directory as earlier modular prototypes.
- **Why it is problematic:**
  - High cognitive load: navigating between safety, RAG retrieval, Pydantic response parsing, and SQLite checkpointing requires scrolling through over a thousand lines.
  - Team merge conflicts: multiple engineers working on different graph nodes modify the same monolithic file.
- **Proposed Simpler Structure:**
  Keep `build_graph.py` clean (under 150 lines), importing node functions from dedicated modules:
  ```
  app/graph/
  ├── nodes/
  │   ├── ingress.py          # entry_router, load_patient_context
  │   ├── safety.py           # safety_assessment, emergency_response
  │   ├── intake.py           # extract_and_merge, adaptive_intake_check, ask_one_question
  │   ├── rag.py              # retrieve_medical_evidence, rerank, context_assembly
  │   ├── synthesis.py        # differential_assessment, citation_validation, persistence
  │   └── actions.py          # ayurvedic_guidance, facilities_service
  ├── state.py                # WorkflowState TypedDict
  └── build_graph.py          # Pure StateGraph assembly & compilation
  ```
- **Refactoring Assessment:** **Worth Doing** for a production team, but keeping it unified was an understandable choice during rapid single-developer prototyping.

---

### Issue 2: Partial Business Logic Duplication in `SessionService.start_session` vs LangGraph
- **Current Structure:**
  In [app/core/session_service.py](file:///home/pruthvi/projects/multiagentrag/app/core/session_service.py#L30-L145), `start_session()` manually executes:
  1. Greeting check (`PatientLookupEngine.check_greeting`).
  2. Safety check (`SafetyEngine.evaluate`).
  3. Semantic cache check.
  4. Symptom extraction (`SymptomExtractor.extract`).
  5. Next question selection (`PatientLookupEngine.select_next_adaptive_question`).
  
  Meanwhile, `process_message()` passes subsequent turns into `compiled_triage_graph.invoke()`, which executes those exact same steps inside graph nodes (`safety_assessment_node`, `extract_and_merge_node`, `adaptive_intake_check_node`).
- **Why it is problematic:**
  - Logic is duplicated across two execution paths: turn 1 runs imperative procedural code in `SessionService`, while turns 2+ run through the declarative LangGraph engine.
  - Bug fixes applied to graph nodes must be manually mirrored in `start_session()`.
- **Proposed Simpler Structure:**
  Unify turn 1 and subsequent turns. `start_session()` should simply initialize the `TriageSession` in the database, and immediately route the initial message through `compiled_triage_graph.invoke()`.
- **Refactoring Assessment:** **High Value**. Eliminates ~100 lines of duplicate orchestration logic and ensures single-path consistency.

---

### Issue 3: Inactive Legacy Facility Discovery Clients
- **Current Structure:**
  In `app/facilities/`, files like `overpass_client.py` and `osm_parser.py` remain alongside the new `scraper.py` (Selenium-based hospital scraper).
- **Why it is problematic:**
  New developers or interviewers examining the repository may be confused about whether OpenStreetMap/Overpass API or Headless Chrome Scraping is the authoritative discovery mechanism.
- **Proposed Simpler Structure:**
  Archive or delete unused OpenStreetMap client files, or cleanly isolate them in an `experimental/` subfolder.
- **Refactoring Assessment:** **Quick Clean-up**. Improves codebase readability and signals clear architectural intent.

---

### Issue 4: Coupling of CPU-Bound Models Inside the Web Application
- **Current Structure:**
  The HuggingFace embedding model (`BAAI/bge-small-en-v1.5`) and the Cross-Encoder (`BAAI/bge-reranker-base`) are loaded directly into the FastAPI process memory via singleton functions in [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py).
- **Why it is problematic:**
  - Memory footprint: Each Uvicorn worker process loads its own PyTorch models into RAM (~1.5GB per worker).
  - CPU competition: Running transformer inference across multiple worker threads competes with FastAPI's event loop handling incoming network sockets.
- **Proposed Scalable Structure:**
  - **Option A (In-Process Optimization):** Run Uvicorn with a single worker and threadpool offloading (current BluCare+ approach), or share model instances using Python `multiprocessing` shared memory.
  - **Option B (Microservice Separation):** Offload embedding and reranking to a specialized model serving container (e.g. TEI — Text Embeddings Inference by HuggingFace, or Triton Inference Server).
- **Refactoring Assessment:** **Premature for Current Scale**. For an MVP serving up to 50 concurrent users, in-process CPU inference with `anyio.to_thread.run_sync` avoids the operational complexity of managing additional Docker containers and network hops.

---

## 3. How to Defend Your Architecture in a System Design Interview

When an interviewer asks: *"Why did you use LangGraph instead of a standard microservice or procedural script?"*

> *"I chose LangGraph because medical triage is fundamentally an iterative, stateful clinical dialogue. Unlike standard single-turn RAG (search -> answer), triage requires:
> 1. Preserving clinical state across turns (reported symptoms, denied signs, severity, duration).
> 2. Conditional branching: an emergency red flag immediately exits to emergency protocols; missing information loops back to ask clarifying questions; complete information triggers the full two-stage RAG retrieval.
> 3. State persistence: LangGraph's checkpointer guarantees that if a network failure occurs mid-dialogue, the patient's case is safely checkpointed in SQLite without data loss.
>
> While a monolithic `build_graph.py` file allowed me to rapidly build and verify the full 11-node workflow with automated tests, in a production team environment I would separate node definitions into dedicated submodules (`nodes/safety.py`, `nodes/rag.py`, `nodes/synthesis.py`) to reduce file length and prevent merge conflicts."*
