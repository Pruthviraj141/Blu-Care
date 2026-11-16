# Multi-Agent RAG Project Summary

This document provides a comprehensive end-to-end technical summary of the Multi-Agent RAG (Medical Triage) project. This summary was synthesized directly by reading the core application source code (FastAPI backend, LangGraph agent workflows, Qdrant retrieval systems, and the frontend JS) and ignores high-level instruction files.

## 1. System Architecture & Entry Points

The system is a Medical Triage Assistant built with **FastAPI** (Backend) and a **Vanilla JavaScript/HTML/CSS** frontend.

- **FastAPI (`app/main.py`)**: Exposes the REST API.
  - **Lifespan/Startup**: Warms up the RAG store (Qdrant client, HuggingFace embeddings, and cross-encoder reranker) before accepting traffic.
  - **Endpoints**: 
    - `POST /session/start`: Initiates a new LangGraph thread and returns a session ID and a welcome message.
    - `POST /session/message`: Sends user messages to the active graph session.
    - `GET /health`: Basic health check.
- **Frontend (`frontend/app.js`)**: A minimalistic interface that captures the user's name, age, and GPS coordinates (Latitude/Longitude). It maintains the session ID and appends `[SYSTEM CONTEXT: User Location...]` to messages to feed geolocation data to the backend. It also parses and renders Markdown (including action buttons like `[ACTION:Find nearby hospitals...]`).

## 2. Agentic Workflow (LangGraph)

The core logic of the application runs on a state machine powered by **LangGraph** (`app/graph/build_graph.py`). It manages a shared `TriageState` object and persists chat history across turns using a checkpointer (attempts Redis, falls back to SQLite).

### State Management (`app/schemas/state.py`)
- The graph maintains a `TriageState` containing: `messages`, `symptom_facts`, `turn_count`, `retrieved_docs`, `possible_conditions`, `stage`, and routing decisions.
- **SymptomUpdates (Pydantic)**: Defines structured data fields extracted from user chats (e.g., `primary_symptom`, `duration`, `severity`, `associated_symptoms`, `symptoms_to_remove`).

### Graph Nodes
The state graph routes between several specific agent nodes:

1. **Central Agent (`app/graph/central_agent.py`)**
   - Acts as the primary router and data extractor. It uses an LLM (temperature=0.2) with a strict structured output schema (`CentralAgentOutput`).
   - Analyzes recent messages to extract clinical facts, update symptoms (or remove denied ones via `symptoms_to_remove`), and makes a routing `decision`.
   - **Decisions**: `ask_question`, `call_rag`, `final_synthesis`, `call_remedy`, `call_facilities`, `post_diagnosis_chat`.
   - **Constraint**: It is explicitly instructed to ask clarifying questions for at least 3-5 turns before triggering RAG to ensure enough symptoms are collected. It employs a rolling summary (`summarize_chat` via a fast LLaMA 3.1 8B model) to prevent hitting context limits.

2. **RAG Retrieval (`app/graph/retrieval.py` & `app/rag/advanced_retrieval.py`)**
   - Reached when the Central Agent has enough facts.
   - Translates structured symptom facts into a dense query string (e.g., "headache for 3 days moderate severity").
   - Leverages **Qdrant** for vector search with score thresholding (to prevent hallucinations on low-confidence matches).
   - Dynamically constructs metadata filters via LangChain's `SelfQueryRetriever` (extracting attributes from natural language, such as Ayurvedic intent).
   - Uses **MMR (Maximal Marginal Relevance)** to diversify results, followed by a **Cross-Encoder Reranker** to precision-sort the final candidates.

3. **Distillation (`app/graph/distillation.py`)**
   - An optimization step acting as an "Intern."
   - Uses a faster/cheaper model (`llama-3.1-8b-instant`) to batch-process all retrieved RAG chunks in parallel.
   - Strips out irrelevant text, extracting only bullet points directly related to the patient's reported symptoms, thereby significantly saving tokens for the synthesis step.

4. **Condition Synthesis (`app/graph/synthesis.py`)**
   - Takes the distilled documents and symptom facts to generate a final medical assessment.
   - Outputs a summary, a `most_likely_condition`, `alternative_conditions`, and recommendations.
   - Hardcoded rules prevent the LLM from stating a diagnosis as absolute certainty.
   - Returns markdown with actionable UI buttons for remedies or finding hospitals.

5. **Remedy Node (`app/graph/remedy.py`)**
   - If the user asks for treatments post-diagnosis, this node runs.
   - Retrieves specific documentation for the predicted conditions and generates a summary of Home/Ayurvedic remedies and general OTC options.
   - Enforces strict rules to explain *why* a remedy helps and lists concrete "red flags to watch for."

6. **Facilities Node (`app/graph/build_graph.py`)**
   - Reached if the user asks for nearby medical help (hospitals/ambulances).
   - Uses tool calling (bound to a `find_nearby_facilities` tool) and leverages the Lat/Lon coordinates appended by the frontend to provide localized Google Maps links.

7. **Post-Diagnosis Chat (`app/graph/build_graph.py`)**
   - Handles general follow-up questions from the user regarding their predicted conditions without triggering the full diagnostic pipeline again.

## 3. Data & RAG Infrastructure

The `app/rag/` directory implements an advanced, multi-stage retrieval pipeline:

- **Embeddings**: Uses `HuggingFaceEmbeddings` (specifically BGE models on CPU/GPU depending on availability). Query texts are correctly prefixed with BGE instruction strings (`app/rag/store.py`).
- **Vector Store**: Connects to **Qdrant** via `qdrant_client`.
- **Reranker**: Uses `sentence_transformers.CrossEncoder` to re-score candidate pairs (Query + Document chunk) for higher precision.
- **Query Constructor**: Uses LangChain's `load_query_constructor_runnable` and `QdrantTranslator` to dynamically map user inputs to strict Qdrant filter schemas (defined in `app/rag/attribute_schema.py`).

## 4. Summary of Tech Stack
- **Framework:** FastAPI, Uvicorn
- **Agent Orchestration:** LangGraph, LangChain
- **LLMs:** Groq API (LLaMA 3.1 70B for reasoning, 8B for fast summarization/distillation)
- **Vector Database:** Qdrant
- **ML Models:** HuggingFace `sentence_transformers` (BGE Embeddings, Cross-Encoders)
- **Persistence:** SQLite (via LangGraph checkpointer `SqliteSaver`) with Redis fallback.
- **Frontend:** HTML5, CSS, Vanilla JS.
