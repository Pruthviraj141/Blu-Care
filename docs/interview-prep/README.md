# BluCare+ Technical Interview Preparation Master Index

Welcome to your comprehensive technical interview preparation suite for **BluCare+**, an AI-powered conversational medical triage and RAG platform.

This documentation suite reverse-engineers the actual repository code to help you explain, justify, debug, and defend your implementation with senior engineering confidence.

---

## Recommended Study Path (Reading Order)

To prepare systematically, follow this 6-step study sequence:

```
Step 1: Understand Architecture ──> [diagrams/README.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/diagrams/README.md)
                                         │
Step 2: Master Technology Stack  ──> [02-tech-stack.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/02-tech-stack.md)
                                         │
Step 3: Deep Dive RAG Pipeline   ──> [03-rag-pipeline.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/03-rag-pipeline.md)
                                         │
Step 4: Know Code & Arch Limits  ──> [04-code-review.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/04-code-review.md) & [05-architecture-review.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/05-architecture-review.md)
                                         │
Step 5: Practice Top 25 Q&As     ──> [06-interview-preparation.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/06-interview-preparation.md)
                                         │
Step 6: Revise Terms & Elevate   ──> [07-glossary.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/07-glossary.md)
```

---

## Document Index

| Step | Document | Purpose & Description |
| :---: | :--- | :--- |
| **1** | [Architecture Diagrams Index](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/diagrams/README.md) | Entry point for 4 interactive HTML architecture and sequence diagrams. |
| **2** | [02-tech-stack.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/02-tech-stack.md) | In-depth breakdown of FastAPI, LangGraph, Qdrant, BGE embeddings, CrossEncoder, ChatGroq, and Clerk. |
| **3** | [03-rag-pipeline.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/03-rag-pipeline.md) | End-to-end trace of ingestion, asymmetric embeddings, vector search, reranking, synthesis, and citation validation. |
| **4** | [04-code-review.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/04-code-review.md) | Evidence-based code review and security audit detailing 6 realistic engineering weaknesses and mitigations. |
| **5** | [05-architecture-review.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/05-architecture-review.md) | Architectural critique of module boundaries, coupling, and realistic refactoring trade-offs. |
| **6** | [06-interview-preparation.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/06-interview-preparation.md) | **Core Manual:** 30s/1m/2m introductions, 25 high-priority technical Q&As, 10x traffic scenarios, code-level deep dives, and quick revision sheet. |
| **7** | [07-glossary.md](file:///home/pruthvi/projects/multiagentrag/docs/interview-prep/07-glossary.md) | 12 key RAG, ML, and systems engineering terms with code locations, examples, and spoken interview answers. |

---

## Interactive HTML Architecture Diagrams

All diagrams have been rendered and validated using **Archify**, backed directly by repository code evidence:

1. [01-system-architecture.html](file:///home/pruthvi/projects/multiagentrag/.archify/01-system-architecture.html): Overall system topology, API gateway, safety firewall, vector store, and AI inference.
2. [02-request-lifecycle.html](file:///home/pruthvi/projects/multiagentrag/.archify/02-request-lifecycle.html): Chronological sequence diagram tracing a patient query from React frontend through RAG retrieval and persistence.
3. [03-conversational-flow.html](file:///home/pruthvi/projects/multiagentrag/.archify/03-conversational-flow.html): Workflow diagram of conversational memory, adaptive follow-up questioning, and the 7-turn completion transition.
4. [04-rag-dataflow.html](file:///home/pruthvi/projects/multiagentrag/.archify/04-rag-dataflow.html): Dataflow topology comparing guideline document ingestion against real-time user query retrieval and reranking.

---

## Key Project Truths for Interviews

1. **Safety is Deterministic:** BluCare+ does **not** rely on LLMs to detect medical emergencies. The `SafetyEngine` evaluates red-flag rules upfront with zero LLM tokens.
2. **Retrieval is Two-Stage:** A fast bi-encoder (`BAAI/bge-small-en-v1.5`) retrieves 20 candidates from Qdrant; a `BAAI/bge-reranker-base` CrossEncoder reranks them down to the top 5 to eliminate false positives.
3. **Embeddings are Asymmetric:** Search queries must be prefixed with BGE's instruction string; passages must not.
4. **State is Checkpointed:** LangGraph uses SQLite WAL mode to guarantee zero conversational state loss between turns.
5. **Citations are Audited:** A regex-based `CitationValidator` ensures every condition and recommendation is backed by a verified document ID.
