# BLUCARE+ — PHASE 2
# Medical Intelligence, RAG Optimization & Evidence-Grounded Assessment

**Role:** Senior AI Engineer, RAG Architect, Medical Knowledge Engineer, Information Retrieval Specialist, and Backend Reliability Engineer.

**Execution mode:** Audit → Baseline → Design → Implement → Evaluate → Integrate → Verify → Document.

**Project:** BluCare+ — AI-Powered Symptom Triage System.

**Primary objective:** Transform the existing medical RAG implementation into a simpler, measurable, reliable medical-evidence retrieval and assessment system.

Do not rebuild the entire application.

Do not change working Phase 1 intake, authentication, safety, or persistence functionality unnecessarily.

The most important requirement is that medical assessments must be grounded in genuine, traceable evidence. When evidence is insufficient, the system must acknowledge that limitation rather than inventing an answer.

---

# 1. PRODUCT CONTEXT

BluCare+ has one focused responsibility:

**Understand symptoms → Assess safety → Retrieve medical evidence → Explain possible conditions → Guide the patient.**

Phase 1 established:

- Clerk authentication.
- Persistent patient-case state.
- Structured symptom extraction.
- Explicit fact corrections.
- Deterministic follow-up questioning.
- Emergency safety checks on every turn.
- Simplified LangGraph orchestration.
- PostgreSQL-backed sessions.
- Integration with the existing RAG assessment pipeline.

Phase 2 is responsible for strengthening the medical intelligence behind that system.

When intake is complete, the system must:

1. Build a medically relevant query from the structured patient case.
2. Retrieve relevant medical passages.
3. Rerank retrieved passages.
4. Assemble a controlled evidence context.
5. Generate an evidence-grounded assessment.
6. Validate every cited reference.
7. Return a structured assessment through the existing API.

## What must remain unchanged

Preserve Phase 1 functionality:

- Authentication and Clerk JWT verification.
- Session ownership.
- PostgreSQL persistence.
- PatientCase schema and provenance.
- Explicit fact correction.
- Question planning.
- Emergency safety engine.
- Existing API contracts.
- Existing frontend compatibility.

Do not rewrite these systems as part of Phase 2.

If a defect in Phase 1 blocks this implementation, document it and make only the minimum necessary compatibility fix. Do not silently change the Phase 1 architecture.

---

# 2. PHASE 2 PRE-FLIGHT AUDIT

Before touching the RAG implementation, inspect the actual current repository.

Read:

- `BLUCARE_PHASE_0_AUDIT.md`
- `BLUCARE_PHASE_1_IMPLEMENTATION.md`
- Existing RAG documentation.
- Existing tests.
- Existing retrieval implementation.
- Existing Qdrant ingestion scripts.
- Existing metadata schema.
- Existing synthesis prompts.
- Existing API response models.

Inspect the actual files, especially:

- `app/rag/store.py`
- `app/rag/advanced_retrieval.py`
- `app/rag/attribute_schema.py`
- `app/graph/retrieval.py`
- `app/graph/synthesis.py`
- `app/graph/distillation.py`
- `app/graph/build_graph.py`
- `app/schemas/state.py`
- `app/schemas/api.py`
- `app/core/config.py`
- Relevant ingestion and verification scripts.
- Existing RAG tests.

The file names above are expected based on the previous architecture audit. Verify the current repository before assuming that all paths remain unchanged.

## Record the current configuration

Determine:

1. Actual embedding model name and revision.
2. Embedding vector dimensions.
3. Query instruction or prefix, if applicable.
4. Document embedding preprocessing.
5. Embedding normalization.
6. Qdrant server version.
7. Qdrant client version.
8. Collection name.
9. Vector distance metric.
10. Collection vector configuration.
11. Current similarity thresholds.
12. Existing metadata fields.
13. Existing CrossEncoder model name and revision.
14. CrossEncoder input limits and truncation behaviour.
15. Candidate retrieval size.
16. Final reranking size.
17. Current ingestion process.
18. Current warm-up and singleton behaviour.
19. Existing retrieval fallbacks.
20. Existing RAG latency, if measurable.

Inspect whether the current medical collection actually contains documents and whether its payloads contain usable source metadata.

Never display API keys, credentials or private medical data in reports.

## Baseline verification

Before changing anything:

- Run existing backend tests.
- Run existing RAG tests.
- Execute the existing retrieval smoke test.
- Check Qdrant connectivity.
- Check collection existence.
- Verify embedding dimensions.
- Verify retrieval results contain the expected payload.
- Run the existing CrossEncoder against representative retrieval examples.
- Execute one complete Phase 1 intake-to-RAG assessment flow.

Record the exact baseline results.

If Qdrant is unavailable, clearly mark the affected integration tests as NOT VERIFIED.

Do not generate artificial success results.

---

# 3. MEDICAL KNOWLEDGE BASE QUALITY

This is the foundation of the entire medical RAG system.

A sophisticated retrieval model cannot compensate for an unreliable knowledge base.

## 3.1 Inspect the existing document corpus

Determine:

- Where the current medical documents originate.
- Which publishers or organizations created them.
- Whether documents are genuine.
- Whether original URLs or identifiers exist.
- Whether publication dates are available.
- Whether update dates are available.
- Whether document versions can be identified.
- Whether duplicate documents exist.
- Whether documents contain outdated guidance.
- Whether the current chunking process preserves the original context.
- Whether any documents are missing source attribution.

Separate verified source information from information that cannot be confirmed.

Do not call a document clinically verified just because it is present in Qdrant.

## 3.2 Introduce a document provenance contract

Create a consistent metadata structure for every medical document.

Suggested metadata:

```python
class MedicalDocumentMetadata:
    document_id: str
    chunk_id: str
    source_id: str

    title: str
    publisher: str

    source_url: str | None
    doi: str | None

    source_type: str | None
    publication_date: str | None
    updated_date: str | None

    jurisdiction: str | None
    population: str | None
    language: str

    clinical_topic: str | None
    section: str | None
    page_number: int | None

    license: str | None
    source_version: str | None
    content_hash: str

    ingestion_version: str
    review_status: str
```

This is a proposed structure. Adapt it to the actual existing document corpus.

Do not create fake URLs, publishers, publication dates, page numbers or verification statuses.

Missing information must be represented as unknown.

## 3.3 Source status

Support clear source states:

- `approved`
- `pending_review`
- `superseded`
- `quarantined`

Only documents eligible under the configured knowledge-base policy may enter normal clinical retrieval.

A document that has been superseded must not silently outrank its newer replacement.

When the corpus contains conflicting versions, preserve the conflict and source information for evaluation and review.

## 3.4 Source selection policy

Inspect available sources before suggesting additional medical sources.

Create a configurable approved-source registry.

The registry should support:

- Publisher identity.
- Original source URL.
- Source type.
- Applicable jurisdiction.
- Document publication or update date.
- Licensing information.
- Approval status.
- Review history.

Do not automatically download or scrape medical information from arbitrary websites.

Do not insert new medical references into the collection without source approval.

Do not assume that a general medical webpage is sufficient evidence for a clinical triage recommendation.

## 3.5 Document ingestion pipeline

Inspect and improve the existing ingestion pipeline.

The ingestion implementation must:

1. Accept approved source documents.
2. Extract their text.
3. Preserve headings and section hierarchy.
4. Preserve page and section references where available.
5. Normalize unnecessary formatting.
6. Detect empty or malformed documents.
7. Identify duplicates.
8. Generate deterministic document and chunk identifiers.
9. Generate reproducible content hashes.
10. Split documents into meaningful chunks.
11. Attach complete provenance metadata.
12. Generate embeddings using the configured embedding model.
13. Store vectors and payloads in Qdrant.

### Chunking requirements

Do not choose arbitrary chunk sizes without examining the existing documents.

Evaluate:

- Token length.
- Section boundaries.
- Paragraph boundaries.
- Heading preservation.
- Table preservation.
- Sentence boundaries.
- Overlap.
- Semantic completeness.

Prefer retaining one coherent medical topic or section in each chunk.

Avoid breaking a clinical recommendation away from its conditions, exceptions or surrounding explanation.

Preserve a path back to the original section and page when the source supports it.

### Idempotent ingestion

The same source should not create duplicate points when ingested twice.

Use:

- Stable identifiers.
- Content hashes.
- Source version tracking.
- Upsert operations.
- Explicit update handling.

Support dry-run mode.

Support ingestion summaries containing:

- Documents discovered.
- Documents accepted.
- Documents rejected.
- Chunks generated.
- Existing chunks unchanged.
- New chunks inserted.
- Old versions superseded.
- Failed documents.

### Collection migration safety

Never delete or overwrite the existing Qdrant collection during an ordinary ingestion run.

If collection schema or embedding model changes are required:

1. Create a versioned collection.
2. Populate it independently.
3. Validate vector dimensions and payload consistency.
4. Run retrieval regression tests.
5. Compare results with the current collection.
6. Switch collection configuration or alias only after successful verification.
7. Retain the existing collection until rollback is no longer needed.

Do not re-embed the entire medical corpus without a documented reason.

---

# 4. EMBEDDING ENGINE — BGE

Keep the existing BGE implementation initially.

Do not replace the model until actual benchmarks demonstrate a meaningful improvement.

## 4.1 Model consistency

The query embedding model and document embedding model must be compatible.

Verify:

- Model name.
- Model revision.
- Vector dimensionality.
- Tokenizer version.
- Preprocessing.
- Normalization.
- Query instruction.
- Document encoding method.

If the current model requires a retrieval instruction, apply it correctly to the query path.

Do not blindly apply an instruction prefix to a model that does not require it.

In particular, verify the existing query prefix against the exact deployed BGE model.

For example, the BGE English v1.5 model family documents:

`Represent this sentence for searching relevant passages:`

Do not change a working prefix without understanding the model-specific requirements.

## 4.2 Embedding singleton

Use one process-local embedding model instance.

Requirements:

- Lazy initialization or explicit startup warm-up.
- No model loading on every request.
- Consistent device selection.
- Graceful initialization errors.
- Predictable memory consumption.
- Correct dimension checks.
- Batch embedding for ingestion.
- Appropriate query encoding behaviour.

Inspect the actual Uvicorn worker count.

Heavy model singletons are process-local. Multiple workers may duplicate model memory.

Do not blindly increase worker count.

## 4.3 Model replacement experiments

Only if the actual current model has a demonstrated limitation:

Evaluate alternatives as separate experiments.

Possible candidates include:

- Existing configured BGE model.
- Another appropriately sized English BGE model.
- BGE-M3 when multilingual retrieval is a genuine product requirement.

A model replacement requires:

- Retrieval benchmark improvement.
- Memory and latency measurement.
- Collection migration strategy.
- Re-embedding strategy.
- Rollback capability.

Never mix vectors generated by incompatible embedding models in the same vector space.

Do not switch the model merely because a newer model exists.

---

# 5. STRUCTURED MEDICAL QUERY CONSTRUCTION

The patient-case state from Phase 1 is the authoritative query input.

Do not reconstruct the patient's medical history by sending the entire conversation transcript to the retrieval system.

Create a dedicated deterministic query builder.

Suggested responsibility:

```python
def build_medical_query(patient_case):
    ...
```

It should produce a predictable query from clinically relevant facts.

Consider:

- Primary symptom.
- Duration and onset.
- Severity.
- Associated symptoms.
- Explicitly absent symptoms.
- Relevant medical history.
- Relevant medications or allergies when useful.
- Applicable demographic context.

## Query requirements

1. Preserve clinically important patient wording.
2. Avoid introducing facts not present in the case.
3. Preserve onset and duration.
4. Preserve important positive and negative symptoms.
5. Avoid irrelevant conversational text.
6. Avoid exposing patient identifiers.
7. Avoid including internal system instructions.
8. Produce a deterministic query representation.
9. Support unit testing without an LLM.
10. Track query-builder version.

Handle negation carefully.

For example:

- "Has fever" and "No fever" must remain distinct.
- "Has difficulty breathing" and "No difficulty breathing" must remain distinct.
- "Pain began yesterday" and "Pain began three weeks ago" must remain distinct.

Do not allow negation to disappear during query construction.

The retrieval query may prioritize present symptoms, but the full relevant case, including denied symptoms, must remain available for reranking and assessment context.

## No LLM self-query dependency

The default retrieval path must not require another LLM call just to generate metadata filters.

Use deterministic filters from structured facts and verified document metadata.

If the existing self-query implementation demonstrably improves retrieval quality, retain it only after measurement. It must never be required for basic retrieval availability.

---

# 6. QDRANT RETRIEVAL ENGINE

Create or simplify a single understandable medical retrieval service.

Suggested interface:

```python
def retrieve_medical_evidence(
    patient_case,
    limit=None,
) -> RetrievalResult:
    ...
```

Adapt the name and signature to existing conventions.

## 6.1 Dense retrieval

The default search flow:

1. Build the structured medical query.
2. Generate its BGE embedding.
3. Validate its vector dimensions.
4. Apply approved deterministic metadata filters.
5. Query Qdrant.
6. Retrieve candidate passages with their payload metadata.
7. Validate the returned payload.
8. Remove inappropriate duplicate results.

Use the currently supported Qdrant query API compatible with the installed server and client.

Prefer `query_points` where supported rather than retaining obsolete APIs without a compatibility reason.

## 6.2 Metadata filtering

Use deterministic Qdrant filters for reliable metadata.

Possible filters include:

- Approved review status.
- Language.
- Jurisdiction.
- Source version status.
- Relevant population when correctly populated.
- Relevant document categories.

Do not apply filters for optional metadata simply because the field exists.

A missing metadata field must not accidentally eliminate every potentially useful document.

Avoid over-filtering that causes important evidence to disappear.

Create Qdrant payload indexes only for fields that are genuinely used in filtering.

Keep indexes consistent with the actual payload types.

## 6.3 Similarity threshold

The old implementation reportedly uses a hardcoded `0.70` similarity threshold.

Do not preserve this blindly.

Determine:

1. The configured vector distance metric.
2. The direction of the score.
3. The actual score distribution.
4. Retrieval results across representative queries.
5. The number of valid results rejected.
6. The number of irrelevant results retained.

Calibrate acceptance thresholds using the evaluation dataset.

Thresholds must be:

- Configurable.
- Documented.
- Versioned.
- Tested.

Do not interpret a vector similarity score as medical confidence.

If no relevant evidence meets the evaluated acceptance criteria, return an insufficient-evidence result.

Do not force five documents into the answer when only one or none are relevant.

## 6.4 Candidate retrieval

Use configurable retrieval limits.

Begin by evaluating the existing candidate size against simpler alternatives.

Do not assume that more candidates automatically improve quality.

Consider:

- Retrieval recall.
- CrossEncoder computation.
- Latency.
- Memory use.
- Duplicate passages.
- Context size.

A reasonable candidate configuration can be established from benchmark measurements.

Do not introduce arbitrary numerical values merely because they are common in online RAG examples.

## 6.5 Duplicate handling

Avoid presenting repeated copies of the same passage.

Use deterministic deduplication.

Consider:

- Chunk ID.
- Content hash.
- Document ID.
- Source version.
- Section identity.

Preserve distinct passages that genuinely contribute additional evidence.

Do not remove two passages merely because their text is similar when they represent materially different populations or recommendations.

---

# 7. CROSS-ENCODER RERANKING

Retain the existing CrossEncoder if it provides measurable retrieval improvement.

Its responsibility is simple:

**Evaluate the relevance between the patient's medical query and each retrieved passage.**

## Pipeline

```text
Qdrant
  |
  v
Candidate passages
  |
  v
CrossEncoder
  |
  v
Relevance ranking
  |
  v
Best evidence passages
```

## Requirements

1. Retrieve candidates using BGE and Qdrant.
2. Construct `(query, passage)` pairs.
3. Score pairs using the configured CrossEncoder.
4. Use batch scoring.
5. Preserve the document's original identity.
6. Sort using the actual reranker output.
7. Return only the configured final evidence set.
8. Preserve source metadata and retrieval trace.

### Score handling

A CrossEncoder relevance score is not automatically a probability.

Some models return unbounded logits.

Do not:

- Present the score as diagnostic confidence.
- Interpret 0.85 as an 85% medical probability.
- Invent confidence values from reranker scores.
- Apply an arbitrary sigmoid and claim clinical calibration.

Use scores for ranking only unless calibration has been independently validated.

### Reranker fallback

If model initialization or inference fails:

- Do not crash unexpectedly.
- Record the failure.
- Preserve the original dense retrieval results.
- Mark the retrieval operation as degraded.
- Apply the configured fallback policy.
- Do not claim that normal reranking was completed.

When evidence quality cannot meet the required minimum, the system must abstain rather than generate a misleading assessment.

### Performance

Measure:

- Model warm-up time.
- Batch scoring latency.
- Number of pairs evaluated.
- Peak memory use where practical.
- Overall retrieval latency.

Do not load a CrossEncoder on every HTTP request.

---

# 8. REMOVE UNNECESSARY RAG COMPLEXITY — THROUGH BENCHMARKING

The existing implementation includes:

- Dense query construction.
- LLM self-query filtering.
- Qdrant search.
- MMR.
- CrossEncoder reranking.
- Separate distillation node.
- Condition synthesis.

The proposed simpler pipeline is:

```text
Patient Case
     |
     v
Structured Query Builder
     |
     v
BGE Embedding
     |
     v
Qdrant Dense Retrieval
     |
     v
CrossEncoder Reranking
     |
     v
Evidence Context Assembly
     |
     v
Grounded Assessment
```

However, do not delete the old components before comparing them.

## Required experiments

Run at least these configurations where the existing implementation permits:

**Configuration A — Existing baseline**

Existing self-query + retrieval + MMR + reranking + distillation + synthesis.

**Configuration B — Simplified retrieval**

Deterministic filters + dense Qdrant retrieval + CrossEncoder + synthesis.

**Configuration C — Without CrossEncoder**

Dense Qdrant retrieval + deterministic filters + synthesis.

**Configuration D — MMR comparison**

Compare MMR-enabled and MMR-disabled candidate selection, with all other conditions held constant.

Compare:

- Retrieval relevance.
- Recall.
- Ranking quality.
- Citation availability.
- Latency.
- Failure rate.
- Context redundancy.
- Output grounding.

If a component provides no meaningful measurable improvement, remove it.

If it improves the results materially, retain it and explain why.

Do not retain an agent merely because it exists in the original architecture.

Do not remove a useful component merely because a simpler architecture looks attractive.

The final architecture should have the fewest components that reliably achieve the required evidence quality.

---

# 9. EVIDENCE CONTEXT ASSEMBLY

The assessment model should receive a clean, bounded and fully traceable evidence context.

Create a dedicated context assembler.

Suggested responsibility:

```python
def assemble_medical_context(
    retrieved_documents,
    max_context_tokens,
):
    ...
```

### Requirements

Each selected passage must include:

- Unique source reference ID.
- Document ID.
- Chunk ID.
- Document title.
- Publisher.
- Publication or update date when available.
- Section and page when available.
- Actual source URL or DOI when available.
- Relevant passage text.

Use an explicit context token budget.

Avoid passing entire medical documents unnecessarily.

Preserve the complete metadata required for citations even when passage content is truncated for model input.

Do not remove caveats from a source while retaining its recommendation.

Preserve conditions, exceptions and population restrictions.

### Prompt injection protection

Retrieved documents are untrusted data.

A medical document, webpage or uploaded reference must not be allowed to change the system prompt.

Instructions embedded within retrieved text must be treated as content, not commands.

The synthesis model must only use the retrieved context as supporting evidence, never as a new instruction source.

Patient text and retrieved documents must remain separate from application-level instructions.

---

# 10. EVIDENCE-GROUNDED MEDICAL SYNTHESIS

This is the main AI output component.

The final model must not simply generate a plausible-sounding medical response.

It must explain what the retrieved evidence supports and where the evidence is insufficient.

Keep the existing Groq integration.

Use the existing configured model initially.

Do not change the LLM provider or add another LLM just for synthesis unless actual benchmarks demonstrate a need.

## 10.1 Assessment generation input

The synthesis function must receive:

1. Validated PatientCase.
2. Relevant patient context.
3. Retrieved and reranked passages.
4. Original source metadata.
5. Existing Phase 1 safety outcome.
6. Explicit assessment constraints.

Do not send unnecessary full conversation history.

## 10.2 Medical synthesis rules

The system prompt must instruct the model:

1. Treat the output as symptom-triage decision support, not definitive diagnosis.
2. Present possible conditions only when supported by the available evidence.
3. Explain why each possibility is being considered.
4. Avoid inventing symptoms or medical history.
5. Distinguish patient-reported facts from retrieved medical information.
6. Acknowledge contradictory or insufficient evidence.
7. Avoid presenting an unsupported possibility as certain.
8. Avoid fabricated medical sources.
9. Avoid invented statistics.
10. Avoid invented probabilities.
11. Avoid personalized prescriptions or drug dosages.
12. Do not override emergency safety decisions.
13. Do not downgrade an emergency safety outcome.
14. Avoid giving reassurance that contradicts the available safety information.
15. Explain uncertainty in plain language.

Do not force the model to return exactly three possible conditions.

It may return fewer possibilities, or none, when the evidence is insufficient.

## 10.3 Assessment schema

Introduce a dedicated Pydantic response model.

Adapt existing schemas rather than duplicating response structures.

Suggested conceptual shape:

```python
class ConditionCandidate:
    name: str
    explanation: str
    supporting_evidence_ids: list[str]
    limitations: list[str]


class EvidenceBasedAction:
    action: str
    rationale: str
    supporting_evidence_ids: list[str]


class MedicalSource:
    source_id: str
    document_id: str
    title: str
    publisher: str | None
    url: str | None
    publication_date: str | None
    updated_date: str | None
    section: str | None
    page_number: int | None


class TriageAssessment:
    case_summary: str

    possible_conditions: list[ConditionCandidate]

    explanation: str

    recommended_actions: list[EvidenceBasedAction]

    warning_signs: list[EvidenceBasedAction]

    urgency: str | None

    sources: list[MedicalSource]

    evidence_limitations: list[str]

    disclaimer: str
```

This is a conceptual schema, not a requirement to introduce every field blindly.

Use existing API fields when possible.

### Important urgency rule

The LLM must NOT independently assign:

- Emergency.
- Urgent.
- Routine.
- Self-care.

Emergency status must be inherited from Phase 1's safety engine.

Any additional clinical urgency category must come from a separately approved, deterministic, clinically reviewed triage policy.

If such a policy is absent, do not fabricate the category.

The API may expose an unavailable or unassessed status according to the existing response contract.

Do not silently call every non-emergency case routine.

---

# 11. CITATION AND SOURCE VALIDATION

This is mandatory.

The existing implementation reportedly returns hardcoded citations. These must not survive into the final assessment.

Replace fabricated citations with actual retrieval references.

## Citation generation

Every medical source displayed in the final assessment must originate from an actual retrieved document.

Generate stable internal IDs for each selected evidence passage.

For example:

```text
[S1] document_123 / chunk_004
[S2] document_456 / chunk_009
```

The model can reference these IDs.

A citation reference must map back to:

- Actual document.
- Actual passage.
- Original source.
- Relevant metadata.

Never allow the model to invent citation IDs or URLs.

## Citation validation

Implement a deterministic post-generation validator.

It must verify:

1. Every referenced ID exists in the supplied retrieval context.
2. Every returned source exists in the database or knowledge base.
3. The citation points to the correct document.
4. The original URL is genuine when present.
5. No unavailable source field is fabricated.
6. Superseded sources are handled according to the source policy.
7. Every material evidence-dependent claim has supporting citations.
8. Unsupported claims are removed, qualified or trigger an abstention.

A valid citation does not automatically prove that a medical claim is correct.

Citation validity and clinical evidence quality must remain separate evaluation dimensions.

### Frontend compatibility

Inspect how the existing frontend renders citations.

Preserve its current contract where possible.

If the frontend expects markdown citation tokens or source objects, adapt the actual backend response without a visual redesign.

Do not change the entire frontend just to introduce a new citation format.

---

# 12. INSUFFICIENT EVIDENCE AND ABSTENTION

This behaviour is extremely important.

A medical RAG system must know when it cannot support an assessment.

Handle the following separately:

**Case A — No retrieval results**

Return an insufficient-evidence result.

**Case B — Low-relevance results**

Do not synthesize a condition from irrelevant passages.

**Case C — Conflicting evidence**

Identify the conflict. Do not silently select whichever passage ranks first.

**Case D — Outdated source**

Do not present superseded guidance as current without a clear explanation and approved policy.

**Case E — Incomplete patient information**

Return to Phase 1 intake when a required fact is still missing.

**Case F — RAG infrastructure unavailable**

Return a controlled service-unavailable response.

Do not create a diagnosis from LLM general knowledge as a fallback.

**Case G — Relevant retrieved evidence but insufficient to distinguish conditions**

Explain what is supported and what remains uncertain.

Do not invent additional conditions merely to fill the output schema.

---

# 13. TRIAGE SAFETY INTEGRATION

Phase 1 owns deterministic emergency detection.

Phase 2 must preserve that authority.

The workflow must be:

```text
Patient Case
    |
    v
Phase 1 Safety Outcome
    |
    v
Evidence Retrieval
    |
    v
Evidence-Based Synthesis
    |
    v
Validated Assessment
```

### Rules

- Emergency sessions must not enter ordinary assessment generation.
- The synthesis model must receive the existing safety outcome as protected structured input where applicable.
- The LLM cannot override the safety engine.
- Warning signs must retain their original safety-rule provenance or medical-source citations.
- Evidence retrieval cannot downgrade an existing emergency.
- A missing RAG result cannot downgrade an existing emergency.

Do not claim that Phase 2 clinically validates the provisional Phase 1 emergency rules.

### Other urgency levels

Prepare a clean integration contract for future clinically reviewed urgency policies.

Keep clinical policy logic separate from the generative assessment model.

If the project currently lacks validated rules for Urgent, Routine and Self-care categories, document that limitation explicitly.

---

# 14. RAG EVALUATION FRAMEWORK

This is what will make BluCare+ technically impressive during interviews.

Do not judge the RAG pipeline using attractive generated answers alone.

We need measurable retrieval and grounding quality.

Create an offline RAG evaluation framework.

Suggested location:

```text
tests/rag/
scripts/evaluate_rag.py
evaluation/rag/
```

Use the existing project structure if a better location already exists.

## 14.1 Evaluation dataset

Create a structured benchmark dataset.

Each test case should support:

- Test case ID.
- Structured patient facts.
- Expected relevant document/chunk IDs.
- Expected clinical topic.
- Expected metadata constraints.
- Whether sufficient evidence exists.
- Whether the case is expected to abstain.
- Dataset provenance.
- Reviewer status.

Use only actual knowledge-base documents and traceable identifiers.

If no medically reviewed ground-truth dataset exists:

- Build the evaluation framework.
- Add software-level test fixtures.
- Mark them as provisional.
- Do not invent clinical gold labels.
- Do not claim clinical validation.

Have clinically qualified reviewers validate medical relevance before treating the benchmark as clinical ground truth.

## 14.2 Retrieval metrics

Measure:

| Metric | Purpose |
|---|---|
| Recall@K | Relevant passages retrieved |
| Precision@K | Retrieved passages that are relevant |
| MRR@K | Position of the first relevant result |
| nDCG@K | Quality of ranking across relevance grades |
| Hit Rate@K | Whether at least one relevant result was retrieved |
| Duplicate Rate | Redundancy in retrieved passages |

Report results separately for different test categories.

## 14.3 Citation metrics

Measure:

- Citation validity rate.
- Citation source-mapping accuracy.
- Claim citation coverage.
- Unsupported citation rate.
- Broken URL rate.
- Missing provenance rate.

## 14.4 Assessment quality

Create a review framework for:

- Faithfulness to retrieved context.
- Unsupported claim rate.
- Correct abstention.
- Handling contradictory sources.
- Relevance to patient facts.
- Preservation of uncertainty.
- Safety policy consistency.

Automated tests must not be presented as clinical validation.

## 14.5 Latency

Measure:

- Query construction.
- Embedding generation.
- Qdrant retrieval.
- CrossEncoder reranking.
- Context assembly.
- Groq generation.
- Citation validation.
- Overall assessment latency.

Report p50 and p95 where the test sample permits meaningful calculation.

Separate model warm-up from steady-state measurements.

## 14.6 Baseline comparison

Compare:

- Existing RAG implementation.
- Simplified candidate implementation.
- MMR enabled and disabled.
- CrossEncoder enabled and disabled.

Use the same benchmark cases, the same document collection and comparable hardware/configuration.

The final report must show actual measurements.

Never invent improved recall, accuracy, latency or citation reliability.

---

# 15. RETRIEVAL CONFIGURATION

Move important retrieval settings into centralized configuration.

Suggested parameters:

```text
RAG_COLLECTION_NAME
RAG_QUERY_TOP_K
RAG_FINAL_TOP_K
RAG_SCORE_THRESHOLD
RAG_RERANKER_MODEL
RAG_RERANKER_ENABLED
RAG_MAX_CONTEXT_TOKENS
RAG_EMBEDDING_MODEL
RAG_EVALUATION_MODE
```

Use project naming conventions.

Ensure threshold units and interpretation are documented.

Do not introduce a huge configuration surface for rarely used controls.

Provide sensible defaults backed by benchmark measurements.

Ensure the project can run tests without downloading every model or contacting external LLM providers.

---

# 16. ERROR HANDLING AND OBSERVABILITY

A retrieval failure must be distinguishable from a valid response with no evidence.

Introduce explicit internal retrieval statuses.

Suggested statuses:

- `success`
- `no_results`
- `insufficient_relevance`
- `reranker_degraded`
- `embedding_failure`
- `vector_store_unavailable`
- `invalid_document_payload`
- `synthesis_failure`
- `citation_validation_failure`

Adapt the final public API carefully to avoid exposing sensitive internal details.

### Logging

Track:

- Request/correlation ID.
- Session ID.
- Retrieval configuration version.
- Embedding model revision.
- Qdrant collection version.
- Candidate count.
- Final passage count.
- Reranking status.
- Source IDs.
- Stage latency.
- Failure category.

Never log:

- API keys.
- Clerk tokens.
- Full patient conversations.
- Unnecessary patient identifiers.
- Full medical case details.

Keep detailed diagnostic information in controlled internal logs.

### Failure policy

- Qdrant unavailable: return a controlled failure.
- BGE unavailable: do not silently use random or incompatible embeddings.
- CrossEncoder unavailable: apply the documented degraded policy.
- Groq unavailable: preserve the session and return a retryable failure.
- Citation validator failure: do not publish fabricated references.
- Invalid Qdrant payload: quarantine or skip the document and record the issue.

Do not turn infrastructure failures into fabricated medical answers.

---

# 17. PERFORMANCE AND DEPLOYMENT

Optimize only where measurements justify it.

Inspect:

- Model loading.
- Process-local singletons.
- Uvicorn worker count.
- Embedding batching.
- CrossEncoder batching.
- Qdrant connection reuse.
- Query timeouts.
- External API retry policies.
- Memory consumption.
- Startup readiness.

Avoid unnecessarily duplicating embedding and reranking models across workers.

Keep retrieval settings compatible with the actual Qdrant server and client versions.

Do not perform an unrelated database redesign.

Do not introduce Redis or additional infrastructure solely for the sake of the RAG pipeline.

---

# 18. TESTING REQUIREMENTS

Create comprehensive tests for the complete Phase 2 system.

All fundamental logic must be testable without live Groq API calls.

## A. Query construction

- Primary symptom is included.
- Duration is included.
- Severity is preserved.
- Important associated symptoms are included.
- Positive and negative symptoms remain distinguishable.
- Missing values are not invented.
- Irrelevant conversation text is excluded.
- Query construction is deterministic.

## B. Embedding

- Query vector dimensions match the collection.
- Correct model is used.
- Query instruction is applied correctly.
- Empty queries fail safely.
- Model initialization is not repeated on every request.
- Incompatible collection configuration is detected.

## C. Qdrant

- Valid query retrieves documents.
- Approved-source filters work.
- Unapproved documents are excluded.
- Missing optional metadata does not eliminate unrelated results.
- Invalid payloads are rejected safely.
- Empty retrieval returns no-results status.
- Deprecated API usage is eliminated where the installed stack supports the replacement.

## D. CrossEncoder

- Correct query-passage pairs are constructed.
- Batch scoring works.
- Results are ordered correctly.
- Original source identifiers are retained.
- Raw scores are not represented as probabilities.
- Failure triggers documented degraded behaviour.

## E. Document ingestion

- Repeated ingestion is idempotent.
- Stable IDs are generated.
- Content hashes are consistent.
- Provenance is preserved.
- Chunking respects source boundaries.
- Unknown metadata remains unknown.
- Superseded documents are handled correctly.
- Failed ingestion does not corrupt the existing collection.
- Dry-run does not mutate the database.

## F. Context assembly

- Selected passages remain within configured token limits.
- Citation identifiers are stable.
- Metadata is preserved.
- Source text remains traceable.
- Duplicate passages are handled correctly.
- Instructions embedded in retrieved content do not modify system behaviour.

## G. Medical synthesis

- Only retrieved evidence is used.
- Unsupported conditions are not invented.
- Fewer than three possibilities are permitted.
- Missing evidence produces appropriate abstention.
- Contradictory information is identified.
- Medical claims have valid supporting citations.
- No fabricated sources are returned.
- LLM output cannot override Phase 1 safety results.
- LLM cannot independently manufacture urgency classifications.

## H. Integration

Run the full Phase 1 → Phase 2 path:

1. Create an authenticated session.
2. Enter symptoms.
3. Collect missing intake facts.
4. Correct an existing fact.
5. Complete intake.
6. Generate the structured query.
7. Retrieve medical evidence.
8. Rerank the evidence.
9. Generate an assessment.
10. Validate citations.
11. Persist the final response.
12. Retrieve the assessment through the existing session history endpoint.

Also test:

- No relevant Qdrant documents.
- Low-relevance results.
- Conflicting documents.
- Superseded sources.
- Qdrant unavailable.
- CrossEncoder unavailable.
- Groq unavailable.
- Invalid structured output.
- Fabricated citation IDs.
- Emergency case reaching the RAG adapter.
- Repeated assessment request.

Emergency cases must remain controlled by Phase 1 and must not proceed into ordinary assessment generation.

---

# 19. PHASE 2 SCOPE RESTRICTIONS

Do not work on:

- React redesign.
- Tailwind design system.
- Landing page.
- Chat UI redesign.
- Hospital finder implementation.
- Google Maps replacement.
- Facilities API.
- Clerk redesign.
- Database migration unrelated to RAG.
- New user-profile features.
- Independent remedy agents.
- General-purpose medical chatbot functionality.
- Mobile UI.
- New autonomous agents.

Nearby hospitals and clinics remain an essential product feature, but their real integration belongs to Phase 3.

Do not remove the existing hospital implementation in this phase.

Do not silently delete Phase 1 modules.

Keep the architecture focused.

---

# 20. REQUIRED CODE ORGANIZATION

Adapt to the actual repository; do not force unnecessary files.

The desired logical separation is:

```text
app/
├── rag/
│   ├── store.py
│   ├── embeddings.py
│   ├── retrieval.py
│   ├── reranker.py
│   ├── query_builder.py
│   ├── context_builder.py
│   ├── document_ingestion.py
│   └── provenance.py
│
├── graph/
│   ├── retrieval.py
│   ├── synthesis.py
│   └── build_graph.py
│
├── schemas/
│   ├── medical_documents.py
│   ├── retrieval.py
│   └── assessment.py
│
└── core/
    └── config.py

scripts/
└── evaluate_rag.py

tests/
└── rag/
    ├── test_query_builder.py
    ├── test_retrieval.py
    ├── test_reranker.py
    ├── test_provenance.py
    ├── test_ingestion.py
    ├── test_synthesis.py
    └── test_end_to_end.py

evaluation/
└── rag/
    ├── README.md
    └── benchmark_schema.json
```

This is a conceptual organization. Reuse appropriate existing modules rather than creating duplicate files.

---

# 21. REQUIRED DELIVERABLES

## A. Actual implementation

Modify the existing codebase.

Do not stop after creating architecture diagrams or recommendations.

## B. Medical knowledge and ingestion documentation

Create:

`BLUCARE_PHASE_2_KNOWLEDGE_BASE.md`

Document:

- Existing medical document corpus.
- Actual sources.
- Existing metadata.
- Source validation policy.
- Document versioning.
- Chunking strategy.
- Ingestion workflow.
- Qdrant collection configuration.
- Limitations.

## C. Retrieval evaluation report

Create:

`BLUCARE_PHASE_2_RAG_EVALUATION.md`

Include:

- Baseline architecture.
- Candidate architecture.
- Benchmark dataset description.
- Retrieval metrics.
- Reranking results.
- Citation measurements.
- Latency measurements.
- Configuration comparison.
- MMR comparison.
- Existing versus simplified pipeline.
- Remaining retrieval weaknesses.

Clearly distinguish automated technical evaluation from clinical validation.

If the necessary ground-truth labels do not exist, report the limitation instead of claiming clinical accuracy.

## D. Implementation documentation

Create:

`BLUCARE_PHASE_2_IMPLEMENTATION.md`

Include:

1. Executive summary.
2. Final RAG architecture.
3. Query-construction implementation.
4. BGE configuration.
5. Qdrant retrieval implementation.
6. Metadata filters.
7. CrossEncoder implementation.
8. Context assembly.
9. Medical source provenance.
10. Citation validation.
11. Structured synthesis schema.
12. Insufficient-evidence behaviour.
13. Phase 1 safety integration.
14. API compatibility.
15. Error-handling behaviour.
16. Performance considerations.
17. Testing results.
18. Known limitations.
19. Clinically unvalidated components.
20. Remaining technical debt.

## E. Configuration

Update `.env.example` with necessary non-secret configuration.

Never overwrite `.env`.

## F. Automated tests

Include the actual test counts and failure details.

## G. Final architecture diagram

Produce an accurate diagram of the implemented RAG and assessment workflow.

Do not describe proposed components as implemented components.

---

# 22. FINAL DEFINITION OF DONE

Phase 2 is complete only when all applicable requirements below have been verified.

| Requirement | Expected result |
|---|---|
| Phase 1 compatibility | Preserved |
| Patient-case query | Deterministic |
| BGE embeddings | Correct and consistent |
| Qdrant retrieval | Functional |
| Metadata filtering | Deterministic |
| Score thresholds | Evaluated and configurable |
| CrossEncoder | Functional and measured |
| MMR | Retained or removed based on measurements |
| Self-query | Retained or removed based on measurements |
| Distillation | Retained or removed based on measurements |
| Source provenance | Traceable |
| Document ingestion | Idempotent |
| Citation validation | Working |
| Grounded synthesis | Schema-validated |
| Unsupported answer handling | Safe abstention |
| Emergency safety integration | Preserved |
| Assessment persistence | Working |
| Existing API | Compatible |
| Retrieval tests | Passing |
| End-to-end tests | Passing |
| Documentation | Complete |

Do not declare success solely because the application starts.

Do not claim improved medical accuracy without a clinically reviewed evaluation process.

Do not report fabricated retrieval metrics.

---

# 23. IMPLEMENTATION EXECUTION RULES

Before implementation, produce a concise plan:

1. Current RAG findings.
2. Existing components to preserve.
3. Components to simplify.
4. Components to remove, with benchmark justification.
5. Files to modify.
6. Files to create.
7. Knowledge-base changes.
8. Collection migration risks.
9. Testing strategy.

Then implement the complete phase without waiting for approval after every small change.

Use current official documentation for the exact installed Qdrant, sentence-transformers, BGE, LangChain and Groq versions.

Do not blindly copy APIs from newer versions when the project uses incompatible versions.

Use official references when relevant:

- Qdrant query API: https://api.qdrant.tech/api-reference/search/query-points/
- Qdrant search: https://qdrant.tech/documentation/search/
- Qdrant indexing: https://qdrant.tech/documentation/manage-data/indexing/
- BGE official implementation: https://github.com/FlagOpen/FlagEmbedding
- BGE embedding model: https://huggingface.co/BAAI/bge-large-en-v1.5
- BGE reranker: https://huggingface.co/BAAI/bge-reranker-v2-m3
- Sentence Transformers retrieve and rerank: https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html

Do not change dependency versions unnecessarily.

Do not expose secrets.

Do not remove existing medical data.

Do not perform irreversible Qdrant collection operations.

Do not claim a feature is complete when it has only been mocked.

---

# 24. FINAL EXECUTION SUMMARY

At the end, provide this table with actual verification evidence:

| Subsystem | Result |
|---|---|
| Existing RAG baseline | Pass / Fail / Not Verified |
| Document provenance | Pass / Fail / Not Verified |
| Document ingestion | Pass / Fail / Not Verified |
| Embedding consistency | Pass / Fail / Not Verified |
| Qdrant retrieval | Pass / Fail / Not Verified |
| Metadata filtering | Pass / Fail / Not Verified |
| CrossEncoder reranking | Pass / Fail / Not Verified |
| Context assembly | Pass / Fail / Not Verified |
| Citation validation | Pass / Fail / Not Verified |
| Grounded synthesis | Pass / Fail / Not Verified |
| Insufficient evidence handling | Pass / Fail / Not Verified |
| Emergency integration | Pass / Fail / Not Verified |
| Assessment persistence | Pass / Fail / Not Verified |
| API compatibility | Pass / Fail / Not Verified |
| Automated tests | Pass / Fail / Not Verified |
| RAG benchmark | Pass / Fail / Not Verified |

Include:

- Total tests passed.
- Total tests failed.
- Total tests skipped.
- Actual retrieval metrics.
- Actual latency measurements.
- Existing versus simplified architecture comparison.
- Important files changed.
- Known bugs.
- Remaining limitations.
- Any manual evaluation still required.

## FINAL INSTRUCTION

Phase 2 should produce a focused medical retrieval and evidence-grounded assessment engine.

The result must be smaller or more justified than the original implementation, not simply more complicated.

**One query builder. One retrieval pipeline. One reranker. One evidence-grounded synthesis process. One authoritative source of medical truth: the approved knowledge base.**

Complete Phase 2, generate all reports, and stop.

Do not start Phase 3.

Wait until the project owner reviews the implementation and explicitly says NEXT.