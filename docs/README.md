# BluCare+ System Documentation & Reports

Welcome to the comprehensive documentation directory for the BluCare+ clinical decision-support and agentic healthcare triage platform.

---

## 📑 Documentation Catalog

### 1. Architecture & System Overview
- **[Complete System Architecture](./BLUCARE_COMPLETE_SYSTEM_ARCHITECTURE.md)**: End-to-end architecture covering state machines, triage workflows, RAG pipeline, and backend services.
- **[Architecture Overview](./arc.md)**: Architectural blueprints and workflow sequence diagrams.
- **[Project Deep Dive](./blucare_project_deep_dive.md)**: Comprehensive technical breakdown of BluCare+ capabilities and system modules.
- **[Summary](./summary.md)**: System summary and milestones overview.
- **[Deployment Guide](./BLUCARE_DEPLOYMENT_GUIDE.md)**: Production deployment instructions, containerization, and environment variables.

### 2. Clinical Reasoning & Multi-Agent Triage
- **[Conversational Clinical Reasoning Report](./BLUCARE_CONVERSATIONAL_CLINICAL_REASONING_REPORT.md)**: Deep dive into clinical triage reasoning, red-flag detection, and dynamic question planning.
- **[Unified Intelligence Implementation](./BLUCARE_UNIFIED_INTELLIGENCE_IMPLEMENTATION.md)**: Synthesis of clinical history, patient profiles, memory lookup, and RAG knowledge.
- **[Analysis Notes](./anaylise.md)**: Clinical analysis and system behavioral notes.
- **[Interview Notes](./INTERVIEW_NOTES.md)**: Stakeholder and clinical workflow interview feedback.
- **[Final Interview Guide](./BLUCARE_FINAL_INTERVIEW_GUIDE.md)**: Comprehensive interview guide and technical talking points.

### 3. Implementation Phases
- **[Phase 0](./phases/phase0.md)**: Initial project setup and infrastructure scaffolding.
- **[Phase 1 Implementation](./BLUCARE_PHASE_1_IMPLEMENTATION.md)** / **[Phase 1 Plan](./phases/phase1.md)** / **[Phase 1 Audit](./phases/phase1_audit.md)**: Core session service, auth, and baseline triage architecture.
- **[Phase 2 Implementation](./BLUCARE_PHASE_2_IMPLEMENTATION.md)** / **[Phase 2 Plan](./phases/phase2.md)** / **[Design System](./phases/phase2_design_system.md)**: Advanced RAG pipeline, Qdrant vector database, and design system.
- **[Phase 2 Knowledge Base](./BLUCARE_PHASE_2_KNOWLEDGE_BASE.md)**: Knowledge ingestion, medical guideline embeddings, and provenance tracking.
- **[Phase 3 Implementation](./BLUCARE_PHASE_3_IMPLEMENTATION.md)** / **[Phase 3 Plan](./phases/phase3.md)**: Facility locator, emergency care routing, and end-to-end integration.

### 4. RAG Quality, Evaluation & Benchmarks
- **[RAG Quality Report](./BLUCARE_RAG_QUALITY_REPORT.md)**: Evaluation of retrieval accuracy, context relevance, and grounded synthesis.
- **[RAG Improvement Report](./RAG_IMPROVEMENT_REPORT.md)**: Detailed report on retrieval reranking, MMR tuning, and citation verification.
- **[RAGAS Evaluation Baseline](./RAGAS_BASELINE_REPORT.md)**: Baseline RAGAS scoring (Faithfulness, Answer Relevance, Context Recall).
- **[RAGAS Evaluation](./RAGAS_EVALUATION.md)** / **[RAGAS General](./RAGAS.md)** / **[RAGAS 2](./ragas2.md)**: RAGAS benchmarking pipelines and evaluation metrics.
- **[RAGAS Failure Analysis](./RAGAS_FAILURE_ANALYSIS.md)**: Root cause analysis of retrieval edge cases and mitigation steps.
- **[Experiment History](./EXPERIMENT_HISTORY.md)**: Historical tracking of hyperparameter changes and evaluation runs.
- **[Reference Sources](./BLUCARE_REFERENCE_SOURCES.md)**: Clinical references, medical guideline provenance, and data sources.

### 5. Performance, Caching & Observability
- **[Redis Cache Implementation](./REDIS_CACHE_IMPLEMENTATION.md)**: Multi-tier semantic and query caching with Redis.
- **[Cache Benchmark Report](./CACHE_BENCHMARK_REPORT.md)**: Latency, hit rates, and throughput benchmarks.
- **[Cache Test Report](./CACHE_TEST_REPORT.md)**: Cache invalidation, TTL, and regression verification tests.
- **[Langfuse Implementation](./LANGFUSE_IMPLEMENTATION.md)**: LLM tracing, prompt versioning, and cost tracking integration.
- **[Langfuse Setup](./LANGFUSE_SETUP.md)** / **[Langfuse Notes](./langfuse.md)**: Configuration and environment setup guide.
- **[Langfuse Test Report](./LANGFUSE_TEST_REPORT.md)**: End-to-end verification of trace propagation and span tracking.

### 6. User Interface, Experience & Design System
- **[BluCare Design System](./BLUCARE_DESIGN_SYSTEM.md)**: Color tokens, glassmorphism specs, typography, and atomic component guidelines.
- **[UI/UX Implementation](./BLUCARE_UI_UX_IMPLEMENTATION.md)**: Implementation of responsive clinical triage interfaces and workflows.
- **[Chat UX Implementation](./BLUCARE_CHAT_UX_IMPLEMENTATION.md)**: Streaming conversation interface, assessment cards, and facility discovery UI.
- **[UI and UX Guidelines](./uiandux.md)**: Design principles and accessibility standards.
- **[Frontend Redesign Prompt](./frontend-redesign-prompt.md)**: Visual specifications and styling prompt.

### 7. Bug Fixes & Regression Documentation
- **[Fix Overview](./fix.md)**: Summary of system fixes and improvements across modules.
- **[Conversation Actions Fix](./BLUCARE_CONVERSATION_ACTIONS_FIX.md)**: Fix for post-assessment action suggestions and clinical follow-ups.
- **[Memory Lookup Fix](./BLUCARE_MEMORY_LOOKUP_FIX.md)**: Resolution of patient memory retrieval and profile context injection.
- **[Clinic Discovery Fix](./CLINIC_DISCOVERY_FIX.md)**: Geolocation parsing and nearby clinic query fixes.
- **[Hospital Discovery Fix](./HOSPITAL_DISCOVERY_FIX.md)**: Overpass API fallbacks and hospital radius search tuning.
