# BluCare+ — Complete Backend Architecture Deep-Dive

> **Purpose of this document**: Give any AI (or human) everything needed to fully understand, reason about, and extend this project without reading every source file. Every claim below was verified against the backend source, not against the README. Where the code is a mock, a stub, or unfinished, this document says so explicitly.

---

## 1. What Is This Project & Why Does It Exist?

**BluCare+** is an **AI-powered medical symptom triage chatbot**. A patient opens the app, describes symptoms in natural language ("I have a headache and fever for 3 days"), and the backend:

1. **Interviews** the patient over several conversational turns and extracts structured medical facts (primary symptom, duration, severity, associated symptoms, age group, pregnancy status, known allergies).
2. **Retrieves** relevant medical reference text from a Qdrant vector database using a four-stage retrieval pipeline.
3. **Distills** the retrieved text down to the clinically relevant fragments (a separate graph node, not a retrieval stage).
4. **Synthesizes** a ranked list of possible conditions with explanations, grounded only in the retrieved context.
5. **Generates remedies** — home remedies, Ayurvedic options, and OTC guidance — from condition-specific retrieval.
6. **Finds nearby facilities** by calling a Selenium-based Google Maps scraper tool.

The project is a **portfolio / demonstration system**, not a clinical product. It has real LLM orchestration, real vector search, and real prompt engineering, wrapped in a large amount of mocked or simplified plumbing (auth, sessions, streaming, hospitals, upload). Those mocks are catalogued in §18.

The user-facing contract is: **a single conversational endpoint that can both ask a follow-up question and, once it has enough facts, run the full RAG → diagnosis → remedy pipeline in the same request.**

---

## 2. Tech Stack

| Layer | Technology | Where |
|---|---|---|
| HTTP framework | **FastAPI** + **Uvicorn** | `app/main.py`, `app/api/` |
| Orchestration | **LangGraph** (`StateGraph`, conditional edges, checkpointer) | `app/graph/build_graph.py` |
| LLM abstraction | **LangChain Core** + **langchain-groq** (`ChatGroq`) | `app/core/llm.py` |
| LLM provider | **Groq** (default `qwen/qwen3.6-27b` in `config.py`; `.env.example` uses `openai/gpt-oss-120b`) | `app/core/config.py` |
| Vector DB | **Qdrant** (`qdrant-client`) | `app/rag/store.py`, `app/rag/advanced_retrieval.py` |
| Embeddings | **HuggingFace BGE** via `langchain-huggingface` / `sentence-transformers` | `app/rag/store.py` |
| Reranking | **Cross-encoder** (`sentence-transformers` `CrossEncoder`) + **MMR** | `app/rag/advanced_retrieval.py` |
| State persistence | LangGraph checkpointers: **Redis** → **SQLite** → **MemorySaver** | `app/graph/build_graph.py` |
| Cache / session backbone | **Redis** (optional, also used by compose) | `app/core/config.py`, `docker-compose.yml` |
| Scraping | **Selenium** (headless Chrome) | `app/rag/tools/facilities_tool.py` |
| Validation | **Pydantic v2** models for API + LLM structured output | `app/schemas/` |
| Packaging | **Docker**, **docker-compose** (backend + frontend + Redis + Qdrant) | `Dockerfile`, `docker-compose.yml` |
| Tests / CI | **pytest**, **flake8**, GitHub Actions | `tests/`, `.github/workflows/` |
| Frontend (out of scope) | React/Vite app served by nginx in compose | `frontend/` |

Notable: the project does **not** use an ORM or a relational database. All session metadata is in-process Python dicts, and conversation state lives in the LangGraph checkpointer (with an in-memory fallback).

---

## 3. Project Directory Structure

```
multiagentrag/
├── app/
│   ├── main.py                  # FastAPI app, middleware, legacy routes, health, lifespan
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # aggregates endpoint routers under the v1 prefix
│   │       └── endpoints/
│   │           ├── session.py   # start / list / delete / history / message / stream
│   │           ├── hospitals.py # nearby facilities + ambulances (both mocked)
│   │           ├── user.py      # profile + settings (in-memory mock)
│   │           └── upload.py    # "document analysis" (JSON-only stub)
│   ├── core/
│   │   ├── config.py            # pydantic-settings Settings object, all defaults
│   │   ├── llm.py               # get_llm() factory (new ChatGroq per call)
│   │   ├── auth.py              # get_current_user / get_optional_user (dev bypass)
│   │   ├── session_service.py   # in-memory session store, graph invocation, fake SSE
│   │   ├── logging.py           # log formatter + CorrelationIdFilter (never attached)
│   │   └── tracing.py           # optional tracing bootstrap (not called by main.py)
│   ├── graph/
│   │   ├── build_graph.py       # StateGraph: 7 nodes, edges, checkpointer selection
│   │   ├── central_agent.py     # fact extraction + routing decision + summarizer
│   │   ├── retrieval.py         # retrieve_condition_docs / retrieve_remedy_docs
│   │   ├── distillation.py      # "intern" node: filter raw docs to relevant facts
│   │   ├── synthesis.py         # final diagnosis markdown
│   │   ├── remedy.py            # home/OTC remedy markdown
│   │   └── ...                  # (node bodies for facilities/post-chat live in build_graph.py)
│   ├── rag/
│   │   ├── store.py             # Qdrant client + embedding + cross-encoder singletons
│   │   ├── advanced_retrieval.py# 4-stage retrieval pipeline
│   │   ├── attribute_schema.py  # metadata field descriptions used by self-query
│   │   └── tools/
│   │       └── facilities_tool.py # Selenium Google Maps scraper (@tool)
│   └── schemas/
│       ├── state.py             # TriageState, CentralAgentOutput, SymptomUpdates, outputs
│       └── api.py               # request/response models
├── scripts/
│   ├── run_cli_chat.py          # CLI harness (initializes tracing)
│   ├── test_advanced_retrieval.py
│   ├── test_api.py
│   ├── test_facilities.py
│   ├── test_rag.py
│   ├── verify_apis.py
│   ├── verify_qdrant_rag.py
│   └── verify_rag.py
├── tests/
│   └── test_api.py              # the only test module; lives at repo root, not under app/
├── frontend/                    # React/Vite UI + nginx Dockerfile (not covered here)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── compiled/stale artifacts: checkpoints.sqlite (+ -shm/-wal), .pytest_cache,
    f.example, .env, skills.txt, summary.md, frontend-redesign-prompt.md,
    arch.html, arc.md, diagrams.html, index.html
```

**Stale artifacts warning:** the repo root and `frontend/src/components/` still contain leftovers from an unrelated cocktail-bar template (`About`, `Cocktails`, `Contact`, `Hero`, `Menu`, `Navbar`) plus built `frontend/dist` output. They are dead weight, not part of BluCare+. Some of them are committed to git.

---

## 4. Application Startup Flow

`app/main.py` is the entry point. Import order matters because the LangGraph is compiled at **module import time**, not during the FastAPI lifespan.

1. **Settings load.** `app/core/config.py` instantiates `Settings()` (pydantic-settings) at import. `.env` is read if present. All values have defaults, so the app starts with no environment at all.
2. **Logging setup.** A formatter is configured. `CorrelationIdFilter` exists but is never added to the logger or formatter, so `%(correlation_id)s` is not actually emitted.
3. **Graph compilation.** `app/api/.../session.py` → `app/core/session_service.py` → `app/graph/build_graph.py`. Because `build_graph.py` ends with `compiled_graph = build_graph()`, the graph is built **before** the ASGI lifespan runs. Checkpointer selection happens here (Redis → SQLite → MemorySaver) and logs via `print()`.
4. **FastAPI app construction.** Middleware is added in this order: `CorrelationIdMiddleware`, then `SecurityHeadersMiddleware`, then `CORSMiddleware`. Starlette applies the last-added middleware outermost, so **CORS runs first**, then security headers, then correlation ID.
5. **Routers.** The v1 router is included, and the **legacy** `/session/start` + `/session/message` routes are declared directly on the app (no auth dependency, no `user_id`).
6. **Exception handlers.** Global handlers convert uncaught exceptions into JSON error responses.
7. **Lifespan startup.** `warm_up()` is called on the RAG store so the embedding model and cross-encoder load once. `init_tracing()` exists but is **never called here** (only `scripts/run_cli_chat.py` calls it).
8. **Shutdown.** Minimal cleanup; the SQLite connection opened for the checkpointer is never explicitly closed.

Consequence of step 3: if the app is imported by tests or a CLI, the graph — and its checkpointer — is created as a side effect of the import.

---

## 5. The LangGraph State Machine — The Core Brain

File: [`app/graph/build_graph.py`](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py)

### 5.1 State Schema — `TriageState`

Defined in `app/schemas/state.py`. It is a `TypedDict` (with an annotated `messages` channel so LangGraph merges message lists rather than replacing them). The fields that matter:

| Field | Type | Meaning |
|---|---|---|
| `messages` | list of LangChain messages | Full conversation. LangGraph's `add_messages` reducer appends. |
| `symptom_facts` | `dict` | Structured facts extracted by the central agent: `primary_symptom`, `duration`, `severity`, `associated_symptoms`, `age_group`, `pregnancy_status`, `known_allergies`. |
| `possible_conditions` | `list` | Populated after synthesis. Once non-empty, the central agent stops showing raw facts back to the LLM and switches to "diagnosis already made" mode. |
| `retrieved_docs` | `list` | Raw docs from `rag_retrieval`, replaced by distilled docs after the distillation node. |
| `stage` | `str` | Routing bookkeeping: `central_agent`, `rag`, `post_prediction`, etc. Used by loop-prevention logic. |
| `turn_count` | `int` | Incremented every time the central agent runs. Drives rolling summarization. |

`CentralAgentOutput` (also in `state.py`) is the structured LLM output:

```python
decision: Literal[
    "ask_question", "call_rag", "final_synthesis",
    "call_remedy", "call_facilities", "post_diagnosis_chat",
]
message: str
symptom_updates: SymptomUpdates
```

Note there is **no `wait_for_user` value** in the literal. `wait_for_user` exists only as a routing target produced by the `else` branch of `route_after_agent()`.

### 5.2 Graph Topology

Seven nodes are registered:

```
START
  │
  ▼
central_agent ──(conditional)──┬──► rag_retrieval ──► distillation ──► condition_synthesis ──► END
                               ├──► condition_synthesis ──────────────────────────────────► END
                               ├──► remedy ───────────────────────────────────────────────► END
                               ├──► facilities ───────────────────────────────────────────► END
                               ├──► post_diagnosis_chat ──────────────────────────────────► END
                               └──► END   (via "wait_for_user")
```

Registered nodes and their jobs:

1. **`central_agent`** — extract facts, merge them into state, decide the next step.
2. **`rag_retrieval`** — run the 4-stage retrieval pipeline, write raw docs to `retrieved_docs`, set `stage="rag"`.
3. **`distillation`** — LLM-filter the raw docs to clinically relevant bullets. **This is a graph node, not a fifth retrieval stage.** It does not change `stage`.
4. **`condition_synthesis`** — produce the diagnosis markdown and set `stage="post_prediction"`.
5. **`remedy`** — retrieve remedy docs for the top 2 conditions and produce remedy markdown.
6. **`facilities`** — call the `find_nearby_facilities` tool and format results.
7. **`post_diagnosis_chat`** — answer follow-up questions after a diagnosis exists.

Key structural fact: **every post-retrieval branch terminates at `END`**. There is no edge back from `condition_synthesis`, `remedy`, `facilities`, or `post_diagnosis_chat` into `central_agent`. Each user turn re-enters the graph at `START`, so multi-turn behaviour comes from the checkpointer restoring `messages`/`symptom_facts`, not from an in-graph loop.

`rag_retrieval → distillation → condition_synthesis` is a fixed chain, not conditional. Distillation cannot be skipped.

### 5.3 Routing Logic — `route_after_agent()`

`route_after_agent(state)` maps the central agent's `decision` to an edge:

| `decision` | Destination |
|---|---|
| `call_rag` | `rag_retrieval` — **unless** `state["stage"] == "rag"`, in which case it short-circuits to `condition_synthesis` (or `wait_for_user` if no docs were retrieved) |
| `final_synthesis` | `condition_synthesis` |
| `call_remedy` | `remedy` |
| `call_facilities` | `facilities` |
| `post_diagnosis_chat` | `post_diagnosis_chat` |
| anything else (incl. `ask_question`) | `wait_for_user`, which is a routing label that maps to `END` |

The loop guard (`decision == "call_rag"` while `stage == "rag"`) is duplicated inside `central_agent_node`, which additionally sets `stage="wait_for_user"` and appends a fallback assistant message. Because no edge returns to `central_agent`, this guard is **defensive and effectively dead** in normal operation — it only matters if someone adds a back-edge later.

**Delta merge in `central_agent_node`:**

1. Apply `symptom_updates.symptoms_to_remove` first, case-insensitively, and only to `associated_symptoms` and `known_allergies`.
2. Union list fields with `list(set(existing + new))` — note this **loses ordering** and can produce nondeterministic prompt ordering.
3. Overwrite scalar fields (`primary_symptom`, `duration`, `severity`, `age_group`, `pregnancy_status`).
4. Set `stage="central_agent"` and increment `turn_count`.

**Rolling summarization:** when `turn_count % 3 == 0` **and** `len(messages) > 4`, `summarize_chat()` is called. It receives only the concatenated **human** messages, not the assistant turns. `summarize_chat()` constructs its own `ChatGroq` (temperature 0.1) with `settings.groq_model` and `settings.groq_api_key`. The comment claims a "faster, cheaper model using the secondary API key"; **`groq_api_key_secondary` is never used anywhere in the codebase.**

One inconsistency worth knowing: the fallback message appended by the loop guard is a plain **dict** `{"role": "assistant", "content": ...}`, while every other message is a LangChain `AIMessage`. `add_messages` tolerates dicts, but downstream code that calls `.content` must handle both.

---

## 6. The Central Agent — Deep Dive

File: [`app/graph/central_agent.py`](file:///home/pruthvi/projects/multiagentrag/app/graph/central_agent.py)

### 6.1 What It Does (Step by Step)

`central_agent_node_impl(...)` is called by the thin `central_agent_node` wrapper in `build_graph.py`.

1. **Slice the conversation.** Only the **last 6 messages** are sent to the LLM. Older context is expected to survive via the checkpointer and the rolling summary; in practice the summary is regenerated only every third turn, so long conversations lose detail between summaries.
2. **Hide facts after diagnosis.** If `possible_conditions` is non-empty, the prompt receives `conditions_text = "Hidden (diagnosis already made)."` instead of the raw condition list, and `predicted_text` marks that a diagnosis already exists. This is what pushes the model toward `post_diagnosis_chat` rather than re-diagnosing.
3. **Hide RAG docs.** Raw `retrieved_docs` are not dumped into the central agent prompt; they are only consumed by synthesis. This keeps the routing prompt small.
4. **Render the prompt** with known facts, conversation, stage, and the "diagnosis exists" flags.
5. **Call the LLM** through `get_llm()`, which returns a **new `ChatGroq` instance on every call** (there is no cache and no module-level singleton — `_llm = None` in `llm.py` is dead code).
6. **Parse structured output** into `CentralAgentOutput`. Parsing is defensive: fenced JSON is stripped, and failures fall back to a safe `ask_question` response rather than crashing the turn.
7. **Merge updates into state** (see §5.3) and append the assistant `message`.

### 6.2 The System Prompt Rules

The prompt (`_CENTRAL_AGENT_SYSTEM_PROMPT`) encodes the triage policy:

- **Act as an interviewer, not a diagnoser.** Ask one focused follow-up question at a time until the minimum fact set is present.
- **Minimum fact set:** primary symptom, duration, severity, associated symptoms, age group, pregnancy status, known allergies. Missing fields drive `ask_question`.
- **Emergency escalation:** chest pain, difficulty breathing, stroke signs, severe bleeding, etc. must produce an urgent message telling the patient to seek emergency care immediately.
- **Tool discipline:** only emit `call_rag` when enough facts exist; only emit `call_remedy` / `call_facilities` / `post_diagnosis_chat` **after** a diagnosis exists (`possible_conditions` non-empty).
- **No hallucinated medicine.** The agent must not name drugs or dosages; that is the remedy node's job, and it is constrained by retrieved text.
- **Structured output only.** The model must return the JSON shape matching `CentralAgentOutput`, including `symptom_updates` (which may be empty).

Because the prompt asks for JSON and the parser is lenient, malformed output degrades to a generic question instead of a 500.

### 6.3 `SymptomUpdates` Schema

```python
class SymptomUpdates(BaseModel):
    primary_symptom: str | None = None
    duration: str | None = None
    severity: str | None = None
    associated_symptoms: list[str] = []
    age_group: str | None = None
    pregnancy_status: str | None = None
    known_allergies: list[str] = []
    symptoms_to_remove: list[str] = []
```

Semantics:

- `None` means "no new information" — it does **not** clear an existing value.
- Lists are **additive** (union), never replacements.
- `symptoms_to_remove` is the only way to delete, and it only works on the two list fields. A wrong scalar (e.g. severity) can only be overwritten, not cleared.
- The model is instructed to copy the patient's own wording, not to normalize into medical terminology.

---

## 7. The 4-Stage RAG Retrieval Pipeline

Files: [`app/rag/advanced_retrieval.py`](file:///home/pruthvi/projects/multiagentrag/app/rag/advanced_retrieval.py), [`app/rag/store.py`](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py), [`app/rag/attribute_schema.py`](file:///home/pruthvi/projects/multiagentrag/app/rag/attribute_schema.py)

This section covers **retrieval only**. Distillation happens afterwards as its own graph node and is described at the end of the section.

### Pipeline Flow:

```
symptom_facts
   │
   ▼
[1] Dense query construction      build_dense_query()
   │
   ▼
[2] Self-query metadata filtering build_filter()  (+ deterministic Ayurvedic filter)
   │
   ▼
[3] Qdrant dense search           score_threshold gate
   │
   ▼
[4] MMR diversification → cross-encoder rerank   (fetch 20 → MMR 10 → top 5)
   │
   ▼
retrieved_docs  ──► distillation node (separate graph node)
```

Entry point: `advanced_retrieve(facts, query_text=None)` returns a list of LangChain `Document` objects. `app/graph/retrieval.py` wraps it as `retrieve_condition_docs()` (for diagnosis) and `retrieve_remedy_docs(condition, query)` (for remedies).

### Stage 1: Dense Query Construction

`build_dense_query(facts)` turns the structured dict into a natural-language query string, concatenating the non-empty facts (primary symptom, duration, severity, associated symptoms, age group). This is deterministic string assembly — **no LLM call**. The goal is a query that embeds close to textbook descriptions of the condition rather than to the patient's conversational phrasing.

If a caller passes an explicit `query_text`, it is used instead of the assembled query (remedy retrieval does this by combining the condition name with the latest user message).

### Stage 2: Self-Query Metadata Filtering

`get_query_constructor()` builds a LangChain `SelfQueryRetriever`-style constructor backed by the Groq LLM, using `attribute_schema.py` to describe filterable metadata fields (e.g. body system, condition category, ayurvedic herbs). The LLM translates the query into a structured `Filter` (equality, `in`, ranges) which `build_filter()` converts into a Qdrant filter object.

Two important behaviours:

- **Deterministic Ayurvedic supplement.** After the LLM filter is built, the code inspects the facts for Ayurvedic indicators and merges an additional `IsEmpty` condition on `metadata.ayurvedic_deep_herbs`. This is a hand-written guard, not model output.
- **Schema drift.** The metadata field `ayurvedic_deep_herbs` is used by the filter code but is **absent from `METADATA_FIELD_INFO`** in `attribute_schema.py`. The LLM is therefore never told that this field exists, and the retriever relies entirely on the hardcoded merge.

If self-query construction fails (LLM error, unparseable filter), `advanced_retrieve` falls back to an unfiltered search rather than returning nothing.

### Stage 3: Qdrant Dense Search + Score Threshold

The dense query is embedded with the configured BGE model and sent to Qdrant.

- `store.py` prepends the BGE query instruction `"Represent this sentence for searching relevant passages: "` to queries (documents are embedded without the prefix). This asymmetry is required for BGE models and is applied in the query path only.
- Results below `score_threshold=0.70` are dropped. **This threshold is hardcoded in `advanced_retrieval.py`; there is no `SCORE_THRESHOLD` environment variable** (a common misreading of the project).
- The call uses `client.search(...)`, which is **deprecated** in current `qdrant-client` versions (the replacement is `query_points`). It still works, but will warn and may break on a future major version.
- Each returned document stores its similarity in `metadata["_score"]`. After reranking, that value is not used for anything, so it is effectively dead metadata.

### Stage 4: MMR → Cross-Encoder Rerank

Retrieval deliberately over-fetches, then narrows:

1. **Fetch** `fetch_k=20` candidates.
2. **MMR** (`maximal_marginal_relevance`, `lambda=0.5`) reduces to `mmr_k=10`, trading relevance against redundancy so near-duplicate textbook paragraphs do not crowd out alternatives.
3. **Cross-encoder rerank** scores each (query, passage) pair directly and keeps `final_k=5`.

The cross-encoder is a `sentence-transformers` `CrossEncoder` loaded once by `store.py`. It is the most expensive step per query, which is why the candidate set is capped before it.

**Latent bug:** `_translator` and `maximal_marginal_relevance` are imported inside `try/except ImportError` and set to `None` on failure, but the code later calls them unconditionally. If the optional dependency is missing, retrieval raises `TypeError: 'NoneType' object is not callable` instead of degrading gracefully.

### After Retrieval: The Distillation Node (not a stage)

`app/graph/distillation.py::distill_rag_docs(symptom_facts, raw_docs)` runs as the `distillation` node between `rag_retrieval` and `condition_synthesis`.

- It instantiates its **own** `ChatGroq` (temperature 0.0) using `settings.groq_model` and `settings.groq_api_key`.
- The docstring calls it "the Intern": a cheap model that reads dense excerpts and keeps only bullets relevant to the patient's symptoms; irrelevant documents yield the literal token `IRRELEVANT` and are discarded.
- If `raw_docs` is empty it returns `[]` immediately.
- It **does not change `stage`** and does not write `possible_conditions`.
- The comments claim an "8B model" and the "secondary API key"; neither is true — the same model and same key as the rest of the app are used.

So the pipeline is **4 retrieval stages + 1 post-retrieval distillation node**, which is why counting "5 stages" is wrong.

---

## 8. The Singleton Store Pattern

File: [`app/rag/store.py`](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py)

Qdrant access is centralized behind module-level singletons:

- `_client` — one `QdrantClient` for the process.
- `_embeddings` — one HuggingFace BGE embedding object.
- `_cross_encoder` — one `CrossEncoder`.

Accessors lazily construct each object on first use and cache it. `warm_up()` forces all three to initialize during FastAPI startup, so the first patient request does not pay model-loading latency.

Why this matters:

- Model loading is expensive (seconds to tens of seconds) and must not repeat per request.
- A single client avoids connection-pool churn against Qdrant.
- Because these are process-local, running Uvicorn with multiple workers (the Dockerfile uses `--workers 2`) creates **one copy per worker** — memory doubles and warm-up happens twice.

Credentials come from `settings.qdrant_url` / `settings.qdrant_api_key`; the collection name is part of the store configuration. Nothing here validates that the collection exists or is populated — a misconfigured `QDRANT_URL` surfaces as an empty result set, not a startup failure.

---

## 9. Condition Synthesis

File: [`app/graph/synthesis.py`](file:///home/pruthvi/projects/multiagentrag/app/graph/synthesis.py)

`condition_synthesis_node` (in `build_graph.py`) calls `synthesize_conditions(...)`.

1. **Inputs:** `symptom_facts` and the distilled `retrieved_docs`. `format_docs_for_prompt()` serializes documents with source metadata into a numbered context block.
2. **Prompt:** `_SYNTHESIS_SYSTEM_PROMPT` mandates that the answer use **only** the retrieved context. It must include: a symptom summary, the most likely condition, alternative possibilities, an explanation of why the leading condition fits, and a recommendation to consult a professional.
3. **Hedging is required by the prompt:** "most likely", "possible", "consistent with" — never a definitive diagnosis.
4. **Insufficient context:** the model is told to say it lacks enough information rather than guess.
5. **Output model:** `ConditionSynthesisOutput` (structured), then formatted into the markdown the frontend displays.

The node also appends machine-readable action lines to the message:

```
[ACTION:Find nearby hospitals for <condition>]
[ACTION:Give me home remedies for <condition>]
```

The frontend parses these and renders clickable cards. They are the only link between the diagnosis message and the `remedy` / `facilities` branches.

Finally the node sets `stage="post_prediction"`, which is what later tells the central agent that a diagnosis already exists. Synthesis **does not** write `possible_conditions`; that is populated from the structured output (the node merges the returned conditions into state).

---

## 10. Remedy Generation

Files: [`app/graph/remedy.py`](file:///home/pruthvi/projects/multiagentrag/app/graph/remedy.py), `remedy_node` in [`app/graph/build_graph.py`](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py)

1. Take the **top 2** entries from `possible_conditions`.
2. For each condition, call `retrieve_remedy_docs(condition, latest_user_message)` — a second trip through the retrieval pipeline with a remedy-oriented query.
3. Combine the documents from both conditions into one context block.
4. Generate structured output with `get_llm(temperature=0.2)`:

```python
class RemedyOutput(BaseModel):
    home_remedies: list[RemedyDetail]       # {name, why_it_helps}
    otc_options: list[RemedyDetail]         # only from retrieved context
    red_flags_to_watch_for: list[str]       # when to seek emergency care
```

5. Format to markdown and set `stage="post_prediction"`.

**Grounding rules in `_REMEDY_SYSTEM_PROMPT`** (this is the liability boundary):

- Every remedy must explain *why* it helps *this* symptom, not just name a folk remedy.
- An OTC drug or drug category may be named **only if it appears in the retrieved text**.
- A dosage may be restated only as "typical guidance is X", never as a personalized prescription.
- If the context supports no medication, the model must say so and offer only rest/general home-care advice.
- `red_flags_to_watch_for` must always be populated with concrete escalation signs.

Remedy retrieval quality is the weak link: if `retrieve_remedy_docs` returns nothing relevant, the model is still forced to produce a schema-valid object, so it tends to fall back to generic hydration/rest advice (which the prompt permits).

---

## 11. Facilities Finder (Hospital/Ambulance Lookup)

Files: `facilities_node` in [`app/graph/build_graph.py`](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py), [`app/rag/tools/facilities_tool.py`](file:///home/pruthvi/projects/multiagentrag/app/rag/tools/facilities_tool.py), [`app/api/v1/endpoints/hospitals.py`](file:///home/pruthvi/projects/multiagentrag/app/api/v1/endpoints/hospitals.py)

There are **two independent implementations**, and only one of them is real.

### 11.1 The graph tool (real scraping, fragile)

`facilities_node`:

1. Requires latitude/longitude. These are injected by the client in a `[SYSTEM CONTEXT]` block in the user message; without them the node returns a canned request for location.
2. Binds the `find_nearby_facilities` tool to the LLM. First call uses `temperature=0`; if the model declines to call the tool, a second call at `temperature=0.3` nudges it. Only the last 4 messages are sent.
3. If the model still refuses, returns a canned "I couldn't find facilities" reply.

`find_nearby_facilities` drives **headless Chrome via Selenium**:

- Builds a Google Maps search URL for hospitals near the coordinates.
- Clicks a "Nearby" button.
- Scrapes result cards using brittle CSS classes: `Nv2PK` (card), `qBF1Pd` (name), `MW4etd` (rating), `UsdlK` (review count), `hfpxzc` (link).
- Returns the **top 5 by rating**.

Failure modes: Google Maps markup changes break the selectors; the scraper has no retry/backoff; and the `python:3.10-slim` Docker image installs **no Chrome/Chromium**, so in Docker this path almost certainly fails. It is a demo-grade scraper, not a production integration.

### 11.2 The REST endpoints (mocked)

`GET /hospitals/nearby` does **not** scrape. It returns a fixed list of four ambulances from `MOCK_AMBULANCES`, identical regardless of the supplied `lat`/`lng`. The ambulance endpoint is equally static. Do not describe this as live data.

---

## 12. Session Management & State Persistence

Files: [`app/core/session_service.py`](file:///home/pruthvi/projects/multiagentrag/app/core/session_service.py), `app/api/v1/endpoints/session.py`

### Session Lifecycle:

Session bookkeeping lives in **module-level Python dictionaries** in `session_service.py` (metadata and ownership maps). There is no database.

**`start_session(user_id, initial_message=None)`**

- Creates a session id, stores metadata (title, created time, owner).
- Title = first 30 characters of the first message + `"..."`; a fixed default title otherwise.
- If `initial_message` is provided, invokes the graph immediately and returns the first assistant message. If not, returns a fixed greeting: `"Hello! I am your AI symptom triage assistant. Describe how you are feeling."`
- Any graph exception is caught and replaced by a canned fallback message — the API never surfaces the traceback.

**`process_message(session_id, user_id, message)`**

- Appends the human message, loads the checkpointed state, invokes `compiled_graph` with `config={"configurable": {"thread_id": session_id}}`, and returns the last assistant message.
- The response includes **hardcoded citations** (`WHO-PCD-901`, `PUBMED-2026-88`), `confidence` from `confidence_score` (default `0.95`), and `risk_level` derived from a naive substring check for `"urgent"` / `"emergency"`. None of this is computed from the retrieved evidence.
- `_SESSION_METADATA` tracks no message count, so `list_user_sessions()` reports a hardcoded `message_count=2` for every session.
- In development, the dev user can list **every** session, not just its own.

**Streaming** (`.../stream`) is **fake SSE**: the full graph response is computed synchronously, split on spaces, emitted chunk-by-chunk with `asyncio.sleep(0.03)`, then terminated with `[DONE]`. There is no token streaming from the LLM and no backpressure.

**`get_session_history`** reads `compiled_graph.get_state(config)` and reconstructs messages for the UI. It fabricates timestamps with `time.strftime("%I:%M %p")` (current time, not message time) and ids `msg_{i}`.

**`delete_session`** removes the metadata and ownership entries only. It **does not delete the LangGraph checkpoint**, so a deleted session's conversation state remains in Redis/SQLite/memory and can be resurrected by reusing the thread id.

### State Checkpointer (Fallback Chain):

At import time `build_graph()` selects the first available checkpointer and logs with `print()`:

1. **Redis** — if `settings.redis_url` is set and Redis is reachable:
   `"Using Redis for state checkpointing (<url>)."`
   Caveat: `langgraph-checkpoint-redis` is **not in `requirements.txt`**, and the code calls `RedisSaver(redis_conn)`, whose signature does not match current releases. In a clean install this branch fails and falls through.
2. **SQLite** — `"Using SQLite for state checkpointing (checkpoints.sqlite)."`
   Caveat: it passes a raw `sqlite3.connect(..., check_same_thread=False)` connection to `SqliteSaver` instead of a context manager, and never closes it. A stale `checkpoints.sqlite` (+ `-shm`/`-wal`) is committed at the repo root.
3. **MemorySaver** — `"Using MemorySaver for state checkpointing."`
   This is the realistic outcome. State is lost on restart and is **per process**.

The process-local fallback interacts badly with the Dockerfile's `--workers 2`: two workers each hold their own `MemorySaver`, so a session's second message can land on a worker that has never seen the first. Single-worker local development is the only reliably consistent mode.

---

## 13. Authentication

File: [`app/core/auth.py`](file:///home/pruthvi/projects/multiagentrag/app/core/auth.py)

Authentication is **effectively disabled**, and the code is honest about it only in comments.

- **`get_current_user`** — verifies a bearer token if present. In `development`/`testing` with no token it returns a dev user (`"dev_authenticated_patient"`). It is imported by `session.py` but **never used as a route dependency**, so it protects nothing.
- **`get_optional_user`** — returns `"dev_authenticated_patient"` whenever the token is missing **or invalid**. All v1 routes depend on this. Shipping this to production means every endpoint is anonymous and every caller shares one identity.
- **Legacy routes** `/session/start` and `/session/message` (declared on the app in `main.py`) have no auth dependency and do not pass a `user_id` at all.

There is no password hashing, no token issuance, no refresh flow, and no per-user authorization check on session access beyond the (bypassable) dev user id. Any real deployment must replace this module.

---

## 14. API Endpoints

All v1 routes live under the v1 router prefix configured in `app/api/v1/router.py` (paths below are relative to it). Request/response models are in `app/schemas/api.py`.

### Session & Chat

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `POST` | `/sessions/start` | Create a session, optionally with a first message | Invokes the graph only if `initial_message` is non-empty |
| `GET` | `/sessions` | List the caller's sessions | `message_count` is hardcoded to 2 |
| `DELETE` | `/sessions/{id}` | Delete a session | Metadata only; checkpoint survives |
| `GET` | `/sessions/{id}/history` | Reconstructed transcript | Fabricated timestamps/ids |
| `POST` | `/sessions/{id}/message` | Main chat turn | Runs the graph; returns hardcoded citations/confidence/risk |
| `GET` | `/sessions/{id}/stream` | SSE endpoint | Fake streaming (space-split + sleeps) |

`ChatMessageRequest.message` has `max_length=2000`; longer input is rejected with 422.

### Hospitals

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `GET` | `/hospitals/nearby` | Nearby hospitals | **Mocked**: same 4 entries for any coordinates |
| `GET` | `/hospitals/ambulances` | Ambulance contacts | **Mocked** static list |

### User

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `GET` | `/user/profile` | Read profile | In-memory dict, mocked defaults (e.g. "Prashik K.") |
| `PUT` | `/user/profile` | Update profile | Not persisted; lost on restart |
| `GET` | `/user/settings` | Read settings | In-memory dict |
| `PUT` | `/user/settings` | Update settings | Not persisted |

### Upload

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `POST` | `/upload/analyze` | "Analyze a medical document" | Accepts `JSONUploadRequest{filename, content}` only — **no multipart file upload**. `ALLOWED_EXTENSIONS` and `extension` are computed but **never validated**. Returns a fixed summary/symptom list. |

### Health Probes

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `GET` | `/health` | Liveness | Always 200 if the process is up; used by the Docker `HEALTHCHECK` |
| `GET` | `/health/live` | Liveness alias | Same idea |
| `GET` | `/health/ready` | Readiness | Checks `bool(settings.qdrant_url)` **only** — it never contacts Qdrant or Redis. Reports `redis_url` and `environment`. |

The readiness probe is therefore a **configuration check**, not a dependency check. A wrong-but-non-empty `QDRANT_URL` still reports ready. `tests/test_api.py` asserts the response contains a `qdrant` key, which is a contract the route must keep even though no ping occurs.

---

## 15. Middleware Stack

Added in `app/main.py`, in this order:

1. **`CorrelationIdMiddleware`** — accepts `X-Correlation-ID` or generates a UUID; sets it on `request.state` and echoes it in the response header. `CorrelationIdFilter` exists in `app/core/logging.py` but is **never attached**, and the log formatter does not include `correlation_id`, so the id never reaches the logs. `LOG_FORMAT` is also unused.
2. **`SecurityHeadersMiddleware`** — adds defensive response headers (e.g. `X-Content-Type-Options`, frame/deny style policies).
3. **`CORSMiddleware`** — allow-list from settings, credentials enabled.

Starlette wraps middleware so the **last added is outermost**: a request traverses CORS → security headers → correlation ID. This matters for preflight `OPTIONS` requests, which short-circuit at CORS before the correlation header is set, and for error responses generated by inner middleware.

---

## 16. Complete User Interaction Flow (End to End)

### Turn 1 — greeting

1. `POST /sessions/start` with no message.
2. `session_service` creates in-memory metadata, returns the fixed greeting. The graph does not run.

### Turn 2 — first symptom

1. `POST /sessions/{id}/message` `{"message": "I have a headache and fever for 3 days"}`.
2. `process_message` appends the human message and invokes `compiled_graph` with `thread_id=session_id`.
3. `central_agent` loads the checkpointed state, slices the last 6 messages, calls the LLM, and extracts `primary_symptom="headache"`, `duration="3 days"`, and `associated_symptoms=["fever"]`.
4. The model still lacks severity/age/pregnancy/allergies → `decision="ask_question"` → `route_after_agent` returns `wait_for_user` → `END`.
5. The assistant's follow-up question is returned. `turn_count=1`.

### Turn 3 — missing facts supplied

1. The patient answers severity and age.
2. `central_agent` merges the new facts (union for lists, overwrite for scalars) and now has enough → `decision="call_rag"`.
3. `rag_retrieval` runs stages 1–4, sets `stage="rag"`, writes ~5 raw docs.
4. `distillation` filters them with a temperature-0 LLM call.
5. `condition_synthesis` produces the diagnosis markdown in the same HTTP response — **there is no separate "diagnose" request**; diagnosis happens inline on the turn that completes the fact set.
6. `possible_conditions` is populated, `stage="post_prediction"`, `[ACTION:...]` lines are appended.

### Turn 4 — remedy request

1. The user clicks "home remedies" (or types it). The frontend sends the message; `central_agent` sees that a diagnosis exists and selects `call_remedy`.
2. `remedy` retrieves remedy docs for the top 2 conditions, generates the grounded markdown, returns.

### Turn 5 — facilities request

1. The client includes `[SYSTEM CONTEXT] lat=... lng=...` in the message.
2. `central_agent` selects `call_facilities`.
3. `facilities` calls the Selenium scraper and formats the top 5 results. Without coordinates it returns a location request instead.

### Turn 6+ — follow-up chat

`post_diagnosis_chat` answers with the diagnosis context visible (temperature 0.4, last 6 messages). It cannot re-run retrieval; if the patient describes a new symptom, the agent must be prompted toward a new `call_rag`.

### Rolling summary

Every third turn with more than four messages, `summarize_chat()` compresses the **human** messages into 2–3 sentences before the next central-agent call.

---

## 17. Data Flow Diagram

```
┌──────────┐   POST /sessions/{id}/message   ┌───────────────────────┐
│ Frontend │ ───────────────────────────────►│ FastAPI (v1 router)   │
└──────────┘                                 │  get_optional_user    │
     ▲                                       └───────────┬───────────┘
     │ SSE / JSON                                        │
     │                                                   ▼
     │                                       ┌───────────────────────┐
     │                                       │ session_service       │
     │                                       │  in-memory metadata   │
     │                                       │  fake SSE splitter    │
     │                                       └───────────┬───────────┘
     │                                                   │ invoke(thread_id)
     │                                                   ▼
     │        ┌────────────────────────────── LangGraph state ──────────────────────────────┐
     │        │                                                                             │
     │        │  central_agent ──► decision                                                 │
     │        │     │  (facts merged, turn_count++, summary every 3rd turn)                  │
     │        │     ├─ call_rag ──► rag_retrieval ──► distillation ──► condition_synthesis ──► END
     │        │     │                   │              │                 │                   │
     │        │     │            Qdrant + BGE     Groq filter      Groq synthesis            │
     │        │     │            + cross-encoder                                            │
     │        │     ├─ call_remedy ─────► remedy (2nd retrieval) ──────────────────────────► END
     │        │     ├─ call_facilities ─► facilities (Selenium) ───────────────────────────► END
     │        │     ├─ post_diagnosis_chat ─► post_diagnosis_chat ─────────────────────────► END
     │        │     └─ ask_question ─────► wait_for_user ──────────────────────────────────► END
     │        └─────────────────────────────────────────────────────────────────────────────┘
     │                                                   │
     │                                       ┌───────────▼───────────┐
     │                                       │ Checkpointer          │
     │                                       │ Redis→SQLite→Memory   │
     │                                       └───────────────────────┘
     │                                                   │
     └───────────────── last assistant message ◄────────┘

External: Groq API (all LLM calls) · Qdrant (vectors) · Google Maps (scraping)
```

---

## 18. Honest Code Quality Assessment

### Strengths ✅

- **Real orchestration.** LangGraph is used properly: typed state, conditional edges, checkpointed threads, and a genuinely useful separation between routing, retrieval, distillation, synthesis, and remedy.
- **Genuine RAG engineering.** Dense query construction, self-query metadata filters, score thresholds, MMR, and cross-encoder reranking are all implemented — not claimed.
- **Prompt discipline.** Synthesis and remedy prompts enforce grounded answers, hedging, and explicit escalation signs. The remedy prompt in particular encodes a sensible liability boundary.
- **Lazy singletons.** Heavy models load once per process and are warmed at startup, which is the right shape for this workload.
- **Defensive LLM parsing.** Malformed structured output degrades to a safe question instead of a 500.
- **Clear schema layer.** Pydantic models for both API and LLM outputs make the contracts readable.
- **Honest fallbacks.** Retrieval failures fall back to unfiltered search; checkpointer selection degrades Redis → SQLite → memory.

### Weaknesses / Areas for Improvement ⚠️

**Correctness & safety**

- **Auth is a bypass.** `get_optional_user` returns a dev identity for missing *or invalid* tokens, and every v1 route uses it. `get_current_user` is never a dependency. Legacy routes have no auth at all.
- **Mocked clinical data presented as real.** `process_message` returns hardcoded citations (`WHO-PCD-901`, `PUBMED-2026-88`), a default confidence of `0.95`, and a risk level from a substring match. `/hospitals/nearby` returns the same four ambulances for any coordinates. `/upload/analyze` performs no analysis. Users could reasonably believe these are computed.
- **Fake streaming.** SSE computes the whole answer, splits on spaces, and sleeps 30 ms per chunk. No token streaming, no cancellation, no real event semantics.
- **Delete is incomplete.** `delete_session` leaves the checkpointer state intact, so a reused `thread_id` resurrects the conversation.
- **Prompt/comment drift.** Both `summarize_chat` and `distill_rag_docs` claim an 8B model and a secondary API key; they use `settings.groq_model` and `groq_api_key`. `groq_api_key_secondary` is dead configuration.

**Reliability & scalability**

- **Process-local state everywhere.** Session metadata is a dict; the realistic checkpointer is `MemorySaver`. Restart loses everything. With `--workers 2` in the Dockerfile, two workers do not share state, so a conversation can appear to "forget" between turns.
- **Checkpointer dependencies are missing.** `langgraph-checkpoint-redis` is absent from `requirements.txt`; `RedisSaver(redis_conn)` does not match the current signature; `SqliteSaver` gets a raw unclosed connection. The advertised Redis path is unlikely to work in a clean install.
- **Readiness doesn't check dependencies.** `/health/ready` only tests that `qdrant_url` is non-empty.
- **No retries or timeouts** around Groq or Qdrant calls; a transient provider error becomes a canned fallback message.
- **The Selenium scraper** depends on Google's CSS class names, has no retry, and the Docker image ships no browser. It cannot work in the deployed container as written.

**Maintainability**

- **Dead or unreachable code:** `_llm = None` in `llm.py`; `CorrelationIdFilter` never attached; `LOG_FORMAT` unused; `init_tracing()` never called by `main.py`; the `call_rag`-while-`stage=="rag"` loop guard is unreachable under current edges.
- **Latent crashes:** `_translator` / `maximal_marginal_relevance` are import-guarded to `None` but then called unconditionally.
- **Deprecated API:** `client.search(...)` instead of `query_points(...)`.
- **Schema drift:** `ayurvedic_deep_herbs` is filtered on but missing from `METADATA_FIELD_INFO`.
- **Inconsistent message types:** the loop-guard fallback appends a `dict` where every other path appends `AIMessage`.
- **Hidden coupling:** the facilities flow depends on a `[SYSTEM CONTEXT]` string embedded in the user's message — an undocumented client contract.
- **Nondeterministic prompt order:** list unions use `list(set(...))`.
- **Committed junk:** `checkpoints.sqlite` (+ `-shm`/`-wal`), `.pytest_cache`, `f.example`, `.env`, `skills.txt`, `summary.md`, `frontend-redesign-prompt.md`, and cocktail-bar frontend components.

---

## 19. Deployment Architecture

Files: [`Dockerfile`](file:///home/pruthvi/projects/multiagentrag/Dockerfile), [`docker-compose.yml`](file:///home/pruthvi/projects/multiagentrag/docker-compose.yml)

**Backend image**

- Base: `python:3.10-slim`.
- Installs `requirements.txt`; runs Uvicorn with `--workers 2`.
- `HEALTHCHECK` curls `/health` (liveness only — it will pass even if Qdrant is unreachable).
- Ships **no Chrome/Chromium**, so the Selenium facilities tool fails at runtime.
- With the `MemorySaver` fallback and two workers, session state is per-worker and inconsistent.

**Compose topology**

| Service | Image / build | Notes |
|---|---|---|
| `backend` | built from `Dockerfile` | `env_file: .env`, `APP_ENV=production`, `REDIS_URL=redis://redis:6379/0`, `QDRANT_URL=http://qdrant:6333` |
| `frontend` | `frontend/Dockerfile`, build context = repo root | served on port 80 via nginx |
| `redis` | `redis:7.0-alpine` | AOF persistence enabled |
| `qdrant` | `qdrant/qdrant:v1.12.1` | vector store; collection must be pre-populated |

Redis is wired but — per §12 — the Redis checkpointer is unlikely to activate without the missing package. Qdrant is required for any diagnosis to work; an empty collection produces empty context and a "not enough information" synthesis.

`APP_ENV=production` also matters for auth: the dev-token bypass in `get_current_user` is gated on non-production, but `get_optional_user`'s bypass is **not** environment-gated, so production remains anonymous.

---

## 20. Key Environment Variables

Read by `app/core/config.py` (pydantic-settings). Defaults exist for everything, so the app boots with an empty environment — which is convenient locally and dangerous in production.

| Variable | Purpose | Notes |
|---|---|---|
| `APP_ENV` | `development` / `testing` / `production` | Affects auth bypasses and log verbosity |
| `GROQ_API_KEY` | Groq credentials | Required for any LLM call |
| `GROQ_API_KEY_SECONDARY` | Intended for cheap-model calls | **Never read by any code path** |
| `GROQ_MODEL` | Model id | `config.py` default `qwen/qwen3.6-27b`; `.env.example` sets `openai/gpt-oss-120b` |
| `QDRANT_URL` | Qdrant endpoint | Also used as the readiness signal |
| `QDRANT_API_KEY` | Qdrant auth | Optional for local |
| `REDIS_URL` | Redis endpoint / checkpointer | Enables the (fragile) Redis branch |
| `LOG_LEVEL` | Logging verbosity | — |

**There is no `SCORE_THRESHOLD` (or similar) env var.** The 0.70 retrieval cutoff, `fetch_k=20`, `mmr_k=10`, `final_k=5`, and `mmr_lambda=0.5` are hardcoded in `advanced_retrieval.py`. Changing retrieval behaviour requires a code edit.

---

## 21. How to Run Locally

1. **Python env**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Note: add `langgraph-checkpoint-redis` and `langgraph-checkpoint-sqlite` yourself if you want persistence beyond `MemorySaver`.

2. **Start Qdrant and load data**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant:v1.12.1
   ```
   Point `QDRANT_URL` at it and populate the configured collection with medical documents whose payloads match `attribute_schema.py`. **Without a populated collection, no diagnosis is possible** — synthesis will correctly report insufficient context.

3. **Configure**
   ```bash
   cp .env.example .env
   # set GROQ_API_KEY, QDRANT_URL, and (optionally) GROQ_MODEL
   ```

4. **Run the API**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Use **one worker** locally. Multiple workers fragment `MemorySaver` state.

5. **Try it**
   - `POST /sessions/start` (or the v1 equivalent) → greeting.
   - `POST /sessions/{id}/message` with symptoms → follow-up questions, then diagnosis.
   - `GET /docs` for the live OpenAPI surface (authoritative route list).

6. **Optional tooling**
   ```bash
   python scripts/run_cli_chat.py          # CLI chat loop; initializes tracing
   python scripts/verify_qdrant_rag.py     # retrieval smoke test
   python scripts/verify_rag.py
   python scripts/test_facilities.py       # requires Chrome + chromedriver
   ```

7. **Tests and lint**
   ```bash
   APP_ENV=testing pytest tests/ -q
   flake8 app --select=E9,F63,F7,F82
   ```
   CI runs flake8 + pytest (with `APP_ENV=testing`), a frontend `npm run build`, and Docker image builds.

---

## 22. Summary for Another AI

If you are extending this project, internalize these facts first:

1. **The graph has seven nodes**, and every branch except `rag_retrieval → distillation → condition_synthesis` terminates at `END`. Multi-turn memory comes from the checkpointer, not from loops.
2. **Retrieval is four stages** (dense query → self-query filter → Qdrant search with a 0.70 cutoff → MMR + cross-encoder rerank). **Distillation is a separate node** after `rag_retrieval`. Do not describe or implement it as "stage 5".
3. **The LLM is not a singleton.** `get_llm()` constructs a new `ChatGroq` per call. `summarize_chat` and `distill_rag_docs` construct their own. `groq_api_key_secondary` is dead.
4. **All thresholds are hardcoded** in `advanced_retrieval.py`. There is no `SCORE_THRESHOLD` env var.
5. **Diagnosis happens inline** on the turn that completes the fact set — one request can return questions, retrieval, and a diagnosis. Remedies and facilities are separate follow-up turns.
6. **Fact merging is additive.** `None` means "no update"; lists union (order-unstable); only `symptoms_to_remove` deletes, and only from `associated_symptoms` / `known_allergies`.
7. **After a diagnosis, the central agent hides the raw condition list and RAG docs** from itself (`"Hidden (diagnosis already made)."`) and routes to `post_diagnosis_chat` unless the user explicitly asks for remedies/facilities.
8. **Auth is a bypass.** `get_optional_user` returns a dev identity for missing or invalid tokens on every v1 route. Replace `app/core/auth.py` before any real deployment.
9. **State is in-process.** Session metadata is a dict; the realistic checkpointer is `MemorySaver`; `delete_session` does not clear checkpoints; two Uvicorn workers do not share state.
10. **Several endpoints are mocks.** `/hospitals/nearby` returns fixed ambulances, `/upload/analyze` does no analysis, citations and confidence are hardcoded, and SSE is a space-split simulation. Do not build features that assume these are real.
11. **The facilities tool is a brittle Selenium scraper** and has no browser in the Docker image. If you need it in production, replace it with a Places API integration.
12. **Where to add things:**
    - New routing behaviour → `CentralAgentOutput` literal + `route_after_agent()` + `_CENTRAL_AGENT_SYSTEM_PROMPT` (all three must agree).
    - New retrieval strategy → `advanced_retrieval.py`, and keep the four-stage contract so callers in `retrieval.py` do not change.
    - New post-diagnosis capability → a new graph node + an `add_edge` to `END` + a decision value in the literal.
    - Persistence → fix the checkpointer branch first (correct saver class, add the dependency, single writer), then session metadata.
13. **Treat the README as aspirational.** This document reflects the code; where they disagree, the code wins.
