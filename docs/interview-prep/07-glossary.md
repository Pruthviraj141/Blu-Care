# Technical Glossary: BluCare+

This glossary defines key technical terms used across BluCare+, showing where each is implemented in the repository, a real-world example, and an interview-ready explanation.

---

### 1. Retrieval-Augmented Generation (RAG)
- **Meaning:** Enhancing an LLM by dynamically fetching relevant external documents from a database and injecting them into the prompt before generating an answer.
- **Where we use it:** [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py#L491-L590) in nodes `retrieve_medical_evidence` and `differential_assessment`.
- **Example:** Looking up NICE clinical guidelines for migraine before advising a patient on headache symptoms.
- **Interview Answer:** *"RAG grounds generative models in authoritative external knowledge, drastically reducing hallucinations and enabling verifiable citations."*

---

### 2. Dense Embeddings
- **Meaning:** Transforming words or passages into a fixed-length numerical vector where semantically similar meanings map to nearby points in multidimensional space.
- **Where we use it:** [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py#L78-L98) with `BAAI/bge-small-en-v1.5` generating 384-dimensional vectors.
- **Example:** The vectors for *"headache"* and *"migraine"* have a high cosine similarity, while *"headache"* and *"fracture"* are distant.
- **Interview Answer:** *"Dense embeddings capture conceptual meaning rather than exact keywords, allowing the system to match user slang with medical terminology."*

---

### 3. Asymmetric Query Prefixing
- **Meaning:** Prepending an instruction string to search queries when using embedding models trained asymmetrically to distinguish questions from passages.
- **Where we use it:** [app/rag/store.py](file:///home/pruthvi/projects/multiagentrag/app/rag/store.py#L117-L126) `embed_query()`.
- **Example:** Prepending `"Represent this sentence for searching relevant passages: "` to `"throbbing headache"`.
- **Interview Answer:** *"Asymmetric prefixing ensures that short user queries and long reference passages map accurately into the same embedding space."*

---

### 4. Cross-Encoder Reranking
- **Meaning:** A secondary neural model that scores a query and document together using full cross-attention across all tokens.
- **Where we use it:** [app/rag/retrieval_service.py](file:///home/pruthvi/projects/multiagentrag/app/rag/retrieval_service.py#L85-L103) with `BAAI/bge-reranker-base`.
- **Example:** Re-scoring 20 candidate medical chunks to place the exact guideline for tension headaches at rank 1.
- **Interview Answer:** *"While bi-encoders provide fast initial retrieval, a CrossEncoder eliminates lexical false positives by modeling deep token-to-token interactions."*

---

### 5. Cosine Similarity
- **Meaning:** A mathematical metric calculating the cosine of the angle between two vectors, measuring directional orientation regardless of vector magnitude.
- **Where we use it:** [app/rag/document_ingestion.py](file:///home/pruthvi/projects/multiagentrag/app/rag/document_ingestion.py#L182) and [app/core/config.py](file:///home/pruthvi/projects/multiagentrag/app/core/config.py#L51) (`score_threshold: 0.55`).
- **Example:** A score of 1.0 means identical direction; 0.0 means orthogonal (unrelated); -1.0 means diametrically opposed.
- **Interview Answer:** *"Cosine similarity measures semantic closeness in vector space, allowing us to filter out passages scoring below 0.55."*

---

### 6. Zero-Token Deterministic Safety Engine
- **Meaning:** A rule-based clinical safety screener executing purely in code without calling an LLM or consuming API tokens.
- **Where we use it:** [app/services/safety_engine.py](file:///home/pruthvi/projects/multiagentrag/app/services/safety_engine.py).
- **Example:** Detecting keywords like `"chest pain"`, `"facial drooping"`, or `"cannot breathe"` and immediately returning emergency ER guidance.
- **Interview Answer:** *"A zero-token safety engine guarantees deterministic, instant emergency interception without latency, token cost, or prompt injection vulnerability."*

---

### 7. StateGraph (LangGraph)
- **Meaning:** A cyclic graph data structure coordinating AI agent workflows, node transitions, and conditional routing edges.
- **Where we use it:** [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py#L1072-L1162).
- **Example:** Routing to `ask_one_question` if facts are missing, or `retrieve_medical_evidence` if the clinical picture is complete.
- **Interview Answer:** *"LangGraph gives us fine-grained control over cyclical multi-turn dialogue loops and state persistence."*

---

### 8. Write-Ahead Logging (WAL Mode)
- **Meaning:** A database optimization where changes are appended to a dedicated write-ahead log file before committing to the main database file.
- **Where we use it:** [app/graph/build_graph.py](file:///home/pruthvi/projects/multiagentrag/app/graph/build_graph.py#L1153) on `checkpoints.sqlite` (`PRAGMA journal_mode=WAL;`).
- **Example:** Prevents database file locking when multiple asynchronous threads checkpoint state simultaneously.
- **Interview Answer:** *"WAL mode enables concurrent reads and writes in SQLite, drastically reducing file-lock contention during session checkpointing."*

---

### 9. Citation Verification (Groundedness)
- **Meaning:** Deterministically validating that source tokens generated by an LLM correspond to actual documents present in the context.
- **Where we use it:** [app/rag/citation_validator.py](file:///home/pruthvi/projects/multiagentrag/app/rag/citation_validator.py).
- **Example:** Checking that `[MED-MIGRAINE-WITHOUT-AURA-02]` in the generated reply matches one of the 5 retrieved documents.
- **Interview Answer:** *"Citation validation prevents fabricated source citations, ensuring every medical recommendation can be audited back to approved guidelines."*

---

### 10. RAGAS (Retrieval Augmented Generation Assessment)
- **Meaning:** An automated evaluation framework that measures RAG quality without ground-truth human annotations.
- **Where we use it:** [evaluation/metrics.py](file:///home/pruthvi/projects/multiagentrag/evaluation/metrics.py) evaluating Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
- **Example:** Mathematically calculating that 95% of factual statements in the assessment are entailed by the retrieved context.
- **Interview Answer:** *"RAGAS provides continuous mathematical evaluation of retrieval precision and synthesis faithfulness during development."*

---

### 11. Semantic Cache
- **Meaning:** Storing query-response pairs in a vector database so semantically equivalent inquiries return instant cached answers without calling an LLM.
- **Where we use it:** [app/services/semantic_cache.py](file:///home/pruthvi/projects/multiagentrag/app/services/semantic_cache.py) using Redis vector search.
- **Example:** The queries *"What are migraine signs?"* and *"Symptoms of acute migraine"* share the same cached answer.
- **Interview Answer:** *"Semantic caching reduces LLM costs and response latency by up to 90% for common educational health questions."*

---

### 12. Haversine Distance Formula
- **Meaning:** A trigonometric equation calculating the great-circle distance between two points on the Earth's surface from their latitude and longitude.
- **Where we use it:** [app/facilities/distance.py](file:///home/pruthvi/projects/multiagentrag/app/facilities/distance.py#L12-L35).
- **Example:** Computing that a clinic at (12.9716, 77.5946) is exactly 2.4 km away from the patient's GPS coordinates.
- **Interview Answer:** *"Haversine distance allows BluCare+ to rank scraped healthcare facilities strictly by geographical proximity to the user."*
