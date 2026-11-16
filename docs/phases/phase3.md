# BLUCARE+ — UNIFIED CONVERSATIONAL INTELLIGENCE & MEDICAL RAG ENGINE
## Complete Root-Cause Fix, Patient Understanding, Adaptive Reasoning & Evidence-Grounded Triage

### ROLE

Act as a Senior AI Architect, LangGraph Engineer, LangChain Engineer, RAG Specialist, Backend Engineer and Healthcare Software Reliability Engineer.

You are modifying an existing application, not building a new chatbot.

Your responsibility is to make BluCare+ genuinely understand a patient's complete consultation, retain their information, retrieve relevant medical evidence, identify possible conditions, and provide appropriate next steps.

**The existing system is malfunctioning. Fix the actual architecture and execution path, not just its prompts.**

---

# 1. THE CORE PROBLEM

The current application exhibits these failures:

1. A complete sentence is sometimes stored as a symptom name.
2. Duration information is repeatedly requested even when already supplied.
3. New symptoms replace or lose previously collected symptoms.
4. The system follows fixed questions instead of understanding the conversation.
5. The final assessment sometimes ignores the patient's actual condition.
6. Generic supportive-care advice is returned without meaningful differential analysis.
7. The RAG pipeline is not sufficiently integrated with the reasoning process.
8. The frontend displays misleading risk or match percentages.
9. Citations are sometimes empty despite an assessment being displayed.
10. The AI behaves like a rigid form instead of a conversational assistant.

Example:

Patient: "I have weakness from last 2 days."

Incorrect behaviour:

"How long have you had this weakness?"

Expected understanding:

- Symptom: Weakness.
- Duration: Two days.
- Status: Present.
- Original wording: "weakness".
- Source: Current message.

The system must understand the complete meaning of a message before deciding what to ask.

---

# 2. FIRST: FIND THE ACTUAL ROOT CAUSE

Trace the complete request lifecycle:

```text
Frontend
  → FastAPI endpoint
  → SessionService
  → LangGraph invocation
  → Memory restoration
  → Message interpretation
  → Patient-case update
  → RAG retrieval
  → Question/assessment decision
  → Response formatting
  → Frontend
```

Inspect the actual implementation of:

- FastAPI session endpoints.
- `SessionService`.
- `build_graph.py`.
- `central_agent.py`.
- PatientCase merging.
- Symptom extraction.
- Question planning.
- PostgreSQL repository.
- LangGraph checkpointer.
- BGE embedding service.
- Qdrant retrieval.
- CrossEncoder.
- Assessment synthesis.
- CitationValidator.
- Frontend API response mapping.

Determine exactly why the frontend receives the wrong question and malformed assessment.

Verify whether the frontend is still calling an old endpoint or legacy graph implementation.

Inspect the actual response returned by the API and compare it with the response rendered in the frontend.

Do not assume that a newly implemented module is being executed just because the file exists.

**Fix the actual running request path.**

Before making changes, run the existing tests and preserve all working Phase 1 and Phase 2 functionality.

---

# 3. ESTABLISH ONE COMPLETE PATIENT CONTEXT

The application must maintain one consolidated patient case for each consultation.

Use the existing PostgreSQL patient-case record as the authoritative source.

Use LangGraph's persistent checkpointer for conversational continuity and workflow state.

The same consultation must always use:

`thread_id = session_id`

Do not create a new thread on every message.

Do not initialize an empty PatientCase on every request.

Do not overwrite existing state with a partial extraction result.

Use the actual installed LangGraph persistence implementation.

Verify `graph.get_state(config)` before invoking subsequent turns and inspect state updates after invocation during debugging.

Use appropriate message reducers such as `add_messages` where required.

Do not append the same messages repeatedly.

Ensure PostgreSQL case versions and checkpoint versions cannot silently diverge.

When the checkpoint is stale, restore the current authoritative patient-case snapshot.

## PatientCase structure

Maintain:

```json
{
  "chief_complaint": null,
  "symptoms": [],
  "medical_history": [],
  "known_conditions": [],
  "medications": [],
  "allergies": [],
  "pregnancy_status": "unknown",
  "relevant_risk_factors": [],
  "patient_preferences": {},
  "question_ledger": {
    "asked": [],
    "answered": [],
    "declined": [],
    "pending": null
  },
  "encounter_summary": null,
  "safety_status": "not_assessed",
  "intake_status": "in_progress",
  "assessment_status": "pending"
}
```

Each symptom must have its own information:

```json
{
  "symptom_id": "uuid",
  "name": "weakness",
  "original_wording": "feeling weak",
  "status": "present",
  "onset": null,
  "duration": {
    "value": 2,
    "unit": "days"
  },
  "severity": null,
  "location": null,
  "progression": null,
  "frequency": null,
  "associated_factors": [],
  "source_message_ids": [],
  "updated_at": null
}
```

This is a conceptual schema. Adapt it to existing Pydantic and database models.

### Important rules

- Store each symptom independently.
- A patient's fever duration must not become the weakness duration unless the message clearly indicates it applies to both.
- Never save an entire natural-language sentence as a symptom name.
- Preserve original wording separately from normalized terminology.
- Keep positive and explicitly negative symptoms separate.
- Never treat an unmentioned symptom as absent.
- Preserve corrections and provenance.
- Merge compatible information instead of replacing the case.
- Mark contradictions rather than silently guessing.

Use a reliable medical terminology normalization mechanism.

Do not hardcode a tiny list of accepted symptoms.

---

# 4. BUILD A CONVERSATIONAL UNDERSTANDING ENGINE

The current extraction behaviour must be replaced or corrected.

Use the existing Groq model through LangChain.

Use Pydantic structured output supported by the installed `ChatGroq` implementation.

Do not create another unnecessary autonomous agent.

The interpreter must receive:

1. Current patient case.
2. Current encounter summary.
3. Pending question.
4. Question ledger.
5. Relevant previous messages.
6. Latest user message.

Its responsibility is to understand the latest message in the context of the complete consultation.

## Required extraction output

Create a structured model containing:

- Intent.
- Chief complaint updates.
- New symptoms.
- Existing symptom updates.
- Explicitly absent symptoms.
- Symptom onset.
- Individual symptom duration.
- Severity.
- Location.
- Progression.
- Frequency.
- Triggers.
- Relevant medical-history updates.
- Medication updates.
- Allergy updates.
- Corrections.
- Answers to pending questions.
- Unknown or declined information.
- Ambiguities.

Example:

Patient:

"I have fever for three days, weakness since yesterday, and mild headache."

Expected extraction:

```json
{
  "symptoms": [
    {
      "name": "fever",
      "status": "present",
      "duration": "3 days"
    },
    {
      "name": "weakness",
      "status": "present",
      "duration": "since yesterday"
    },
    {
      "name": "headache",
      "status": "present",
      "severity": "mild"
    }
  ]
}
```

Do not assign the same duration to all symptoms unless supported by the patient's wording.

## Message interpretation

Recognize:

- Greetings.
- Symptom descriptions.
- Answers to questions.
- Multiple answers in one message.
- Corrections.
- Negative symptoms.
- Questions about medical information.
- New symptoms after assessment.
- Requests for Ayurvedic information.
- Requests for nearby medical facilities.

A greeting must not trigger unnecessary medical reasoning or a fake LOW RISK label.

A correction must update the appropriate existing fact.

A new symptom must be added without deleting existing symptoms.

---

# 5. INTELLIGENT QUESTION ENGINE — NO FIXED QUESTIONNAIRE

This is a critical requirement.

Remove the universal fixed sequence of:

`Primary symptom → Duration → Severity → Associated symptoms`

It must not control the conversation.

The next question must depend on:

- Current patient facts.
- Current symptoms.
- Previous answers.
- Explicitly denied symptoms.
- Relevant medical history.
- Previous questions.
- Current pending question.
- Retrieved medical evidence.
- Applicable clinical guidance.

Use an intelligent question-planning step.

The planner should identify:

1. What is already known?
2. What is genuinely unknown?
3. Which missing fact is clinically relevant?
4. Which question would contribute most to understanding the case?
5. Can assessment proceed without another question?

The LLM can propose one relevant question.

Python must validate it before returning it.

## Semantic question memory

Track stable information identifiers instead of literal question text.

Examples:

- `fever.duration`
- `fever.severity`
- `weakness.duration`
- `weakness.progression`
- `headache.location`
- `headache.severity`
- `associated.nausea`

Before asking:

- Check existing patient facts.
- Check answered question IDs.
- Check pending question.
- Check declined information.
- Check whether the latest message already answers the requested fact.
- Check semantically equivalent questions.

For example:

"How long have you had fever?"

and:

"When did your fever start?"

must not be asked as separate questions when the duration is already known.

Do not compare question strings only.

Allow one focused question per response.

Accept multiple answers within one user message.

If the patient says they do not know, record unknown and avoid asking the same question indefinitely.

If clarification is genuinely necessary, ask one clear question.

---

# 6. SHORT CENTRALIZED SYSTEM PROMPTS

The entire application must not depend on one enormous system prompt.

Centralize a few small prompts in one prompt module.

Keep domain behaviour in deterministic Python services, schemas, retrieved evidence and runtime context.

Use these concise role definitions.

### A. Encounter Interpreter

"You understand the patient's latest message using the complete relevant consultation context. Extract all new symptoms, facts, negatives, answers and corrections. Preserve the patient's meaning, normalize medical terms, and never invent missing facts. Return validated structured information only."

### B. Clinical Assessor

"Assess the complete patient case against the supplied retrieved medical evidence. Identify supported possible conditions, explain supporting and conflicting findings, acknowledge uncertainty and cite only supplied evidence IDs. Never invent diagnoses, probabilities, sources or urgency classifications. Abstain when evidence is insufficient."

### C. Care Advisor

"Provide relevant conventional, general and Ayurvedic care information using the supplied patient context and verified sources. Check allergies, medications, conditions and relevant contraindications. Distinguish traditional use from demonstrated evidence. Never invent remedies, dosages or safety claims."

### D. Follow-up Assistant

"Answer the patient's question using the current patient case, previous assessment and verified sources. Preserve established context, recognize new symptoms and corrections, and escalate safety concerns through the existing safety workflow."

Do not repeat application architecture, API rules or enormous medical questionnaires inside every prompt.

Provide relevant structured runtime context when each node executes.

---

# 7. MAKE RAG THE CORE OF MEDICAL REASONING

The RAG system must actively participate in understanding the patient's situation.

It must not merely run after fixed questions and append generic advice.

Preserve the existing Phase 2 implementation:

- BGE embeddings.
- Qdrant.
- CrossEncoder reranking.
- Medical source provenance.
- CitationValidator.
- Evidence-context assembly.

Do not reintroduce unnecessary self-query agents or distillation agents.

## 7.1 Contextual query construction

Create the retrieval query using the complete updated patient case.

Include:

- All present symptoms.
- Individual symptom durations.
- Severity.
- Onset.
- Progression.
- Important negative symptoms.
- Relevant medical context.

Preserve negation.

Do not send only `primary_symptom`.

Do not embed the full raw conversation when a structured query is sufficient.

## 7.2 Retrieval during intake

Introduce an evidence-aware intake process.

After extracting and merging a clinically meaningful new message:

1. Determine whether the medical query has changed.
2. Reuse cached retrieval only when the structured case hash and retrieval configuration are unchanged.
3. Otherwise query BGE and Qdrant.
4. Rerank relevant passages through CrossEncoder.
5. Make retrieved evidence available to the question planner.

This allows follow-up questions to be informed by relevant medical guidance rather than a universal questionnaire.

For example, the retrieved evidence may identify which additional patient information is relevant to distinguishing supported conditions.

Only ask questions grounded in the actual clinical context.

Do not use retrieved documents as system instructions.

## 7.3 Final retrieval

When sufficient intake information is available:

1. Refresh retrieval using the latest complete case.
2. Retrieve relevant medical documents.
3. Apply deterministic approved metadata filters.
4. Rerank the candidates.
5. Remove inappropriate duplicates.
6. Assemble a bounded medical evidence context.
7. Pass actual source IDs and supporting passages into the assessor.

The final assessment must not rely on stale evidence from an earlier incomplete patient case.

## 7.4 Condition identification

Use retrieved medical documents as the source of possible conditions.

Extract candidate conditions from actual relevant document content and metadata.

Compare the complete patient case against the evidence.

For each condition evaluate:

- Symptoms matching.
- Symptoms that contradict the possibility.
- Duration compatibility where documented.
- Relevant risk factors.
- Missing information.
- Source quality.
- Evidence limitations.

Return up to three supported possibilities.

Do not hardcode a disease list in the system prompt.

Do not fabricate a list of diseases to fill the response.

Do not present a similarity score as diagnostic probability.

Do not diagnose with certainty.

## 7.5 Knowledge-base coverage

Inspect the actual indexed medical corpus.

The documented corpus includes:

- Tension-type headache.
- Acute migraine without aura.
- Viral pharyngitis and upper respiratory infections.
- Viral gastroenteritis and dehydration prevention.
- Acute bronchitis and cough assessment.

Create a disease/topic coverage report.

Identify whether fever and generalized weakness are sufficiently supported across relevant conditions.

If evidence is missing, identify specific knowledge gaps and propose ingestion from genuine, appropriate, accessible medical sources after provenance and licensing review.

Do not claim that an unsupported medical topic is covered.

Do not invent diagnoses from the LLM's general knowledge when the retrieval context is insufficient.

## 7.6 Retrieval quality

Keep:

`BGE → Qdrant → CrossEncoder → Evidence Context`

Measure retrieval relevance, citation validity and latency.

Do not display CrossEncoder or embedding scores to patients as disease probabilities.

---

# 8. FINAL DIFFERENTIAL ASSESSMENT

The final assessment should explain what the patient may be experiencing based on the collected information and retrieved references.

Use structured Pydantic output.

Suggested contract:

```python
class TriageAssessment:
    case_summary: str

    urgency: str | None

    possible_conditions: list

    explanation: str

    matching_findings: list

    conflicting_findings: list

    uncertainties: list

    recommended_actions: list

    general_care: list

    conventional_guidance: list

    ayurvedic_guidance: list

    warning_signs: list

    sources: list

    evidence_limitations: list

    disclaimer: str
```

Adapt existing models rather than creating duplicates.

### Assessment rules

- Use the entire structured patient case.
- Do not repeat malformed raw symptom sentences.
- Normalize medical terms for presentation.
- Explain each possible condition.
- Do not force three conditions.
- Show genuine supporting evidence.
- Mention missing or conflicting evidence.
- Avoid unsupported medical reassurance.
- Do not generate fake confidence percentages.
- Do not generate fake citations.
- Do not force generic home-care advice.
- Do not prescribe medication.

A missing citation must remain missing, not be replaced by a fake source.

If evidence is inadequate, return an explicit insufficient-evidence assessment.

---

# 9. URGENCY AND EMERGENCY SAFETY

Maintain Phase 1's deterministic safety engine.

Run it on every message.

It must evaluate both the original message and the updated structured case.

Emergency outcomes cannot be overridden by retrieval or LLM generation.

Do not display LOW RISK merely because no obvious emergency keyword was matched.

Use:

- `NOT_ASSESSED`
- `EMERGENCY_DETECTED`
- An approved assessed category where an appropriate clinical protocol exists.

Urgent, Routine and Self-care classification must be based on an approved clinical policy, not LLM opinion.

Never label an incomplete assessment as safe.

Never make hospital search a prerequisite for emergency guidance.

Do not allow the model to invent emergency rules.

---

# 10. CARE RECOMMENDATIONS: CONVENTIONAL + AYURVEDIC

Include general, conventional and Ayurvedic information in the final product without creating unnecessary autonomous agents.

## General care

Use relevant source-supported home-care information.

## Conventional medical information

Provide general information about professional treatment options and OTC categories only when supported by the medical evidence.

Consider:

- Existing medications.
- Allergies.
- Medical conditions.
- Pregnancy where relevant.
- Contraindications.

No personalized prescriptions or invented dosages.

## Ayurvedic information

Ayurvedic care is an additional capability, not a replacement for necessary medical treatment.

Use a separate Ayurvedic evidence retrieval query or a verified appropriate collection.

Retrieve only genuine documents with provenance.

Distinguish:

- Traditional use.
- Evidence-supported information.
- Limited evidence.
- Unknown effectiveness.
- Known safety concerns.

Never invent herbs, formulations, dosages or interactions.

Do not recommend unverified herbo-mineral preparations.

Do not recommend potentially toxic products.

If sufficient evidence and safety information are unavailable, explicitly say that no reliable recommendation can be made.

Do not automatically recommend Ayurveda for every possible condition.

Use patient preference where known.

The following reference sources may be used for safety context, but they are not evidence of efficacy for a particular remedy:

- https://www.nccih.nih.gov/health/ayurvedic-medicine-in-depth
- https://www.nccih.nih.gov/health/safety
- https://ods.od.nih.gov/

All medical and Ayurvedic content must retain its actual source provenance.

---

# 11. FINAL TWO PATIENT ACTIONS

After a completed assessment, return two functional actions associated with the selected possible condition:

**1. Explore Ayurvedic guidance**

- Pass the selected condition ID.
- Retrieve relevant Ayurvedic evidence.
- Check the patient's context.
- Validate sources.
- Generate a safe, clearly qualified response.
- Abstain when evidence is insufficient.

**2. Find nearby clinics**

- Use the existing free OpenStreetMap + Overpass integration.
- Return genuine mapped hospitals and clinics.
- Calculate approximate straight-line distance.
- Preserve OSM attribution.
- Include Google Maps Search URLs for broader local discovery.
- Never scrape Google Maps.
- Never fabricate facilities.

Both actions must be mapped to actual backend API operations and existing LangGraph routing.

Validate that the selected condition belongs to the active assessment.

Do not allow the actions to override emergency guidance.

Conventional care information must also be included in the assessment when supported, rather than hidden behind the two actions.

---

# 12. REQUEST AND TOKEN OPTIMIZATION

Do not repeatedly send the full transcript or enormous system prompts.

Use:

- Authoritative patient-case snapshot.
- Pending question.
- Relevant question history.
- Compact encounter summary.
- Latest message.
- Relevant retrieved passages.

Token-efficient target:

| Operation | Strategy |
|---|---|
| Greeting | Deterministic; zero LLM calls |
| Simple answer to pending question | Deterministic parsing where reliable |
| Complex message | One structured interpreter call |
| Case merging | Python |
| Safety rules | Python |
| Memory lookup | Python |
| Retrieval | BGE + Qdrant |
| Reranking | CrossEncoder |
| Question planning | One contextual LLM call when necessary |
| Final assessment | One synthesis call |
| Citation validation | Python |

Do not force an expensive LLM call for every trivial message.

Do not compromise patient understanding just to enforce an artificial one-call limit.

Reuse recent evidence when the case query and retrieval version remain unchanged.

Record actual provider token usage where available.

---

# 13. GRAPH ARCHITECTURE

Use one understandable LangGraph workflow.

```text
START
  |
  v
Load Persistent Patient Context
  |
  v
Raw Message Safety Check
  |
  v
Interpret Latest Message
  |
  v
Merge Updated Patient Case
  |
  v
Updated Safety Check
  |
  +---- Emergency ---> Persist Emergency Response ---> END
  |
  v
Context and Memory Lookup
  |
  v
Evidence Retrieval
  |
  v
Adaptive Clinical Decision
  |
  +---- Clarification Required ---> Ask One Question ---> END
  |
  +---- More Information Needed ---> Ask One Question ---> END
  |
  v
Refresh Final RAG Evidence
  |
  v
Differential Assessment
  |
  v
Citation Validation
  |
  v
Generate Structured Care Information
  |
  v
Persist Assessment
  |
  v
Return Assessment + Patient Actions
  |
  v
END
```

Use deterministic Python nodes for state, safety and validation.

Use LLM calls for language understanding and medical evidence synthesis.

Do not create a separate agent for every step.

Do not create uncontrolled graph loops.

Do not introduce multiple conflicting sources of patient memory.

---

# 14. FRONTEND INTEGRATION

Do not redesign the UI.

Inspect the existing frontend contract.

Fix only the response mapping and action handlers necessary to display:

- Correct normalized symptoms.
- Correct patient-case summary.
- Correct urgency status.
- Evidence-supported possible conditions.
- Supporting citations.
- Recommended actions.
- General care.
- Conventional guidance.
- Ayurvedic guidance.
- Warning signs.
- The two functional actions.

Remove misleading `85% Match` and `LOW RISK` display values when no meaningful validated category or probability exists.

Do not display zero-citation assessments as evidence-grounded reports.

Ensure the frontend is not displaying stale responses from an earlier request.

Ensure action clicks send the correct session ID, assessment ID, action ID and condition ID.

Preserve the existing visual design.

---

# 15. ACTUAL REGRESSION TESTS

Do not test only isolated functions.

Test the real API and graph flow used by the frontend.

## Test A: Full sentence extraction

Patient:

"I have weakness from last 2 days."

Expected:

- Symptom = weakness.
- Duration = 2 days.
- Primary complaint = weakness.
- No question asking when weakness started.

## Test B: Multiple symptoms

Patient:

"I have fever for three days, weakness since yesterday and mild headache."

Expected:

- Fever duration = 3 days.
- Weakness duration = since yesterday.
- Headache = present.
- No incorrect shared duration.
- All three symptoms preserved.

## Test C: Pending answer

Patient:

"fever"

Assistant:

"When did it start?"

Patient:

"two days ago"

Expected:

- `fever.duration = 2 days`.
- No restart of primary-symptom intake.

## Test D: New symptom

Patient:

"I also feel weak."

Expected:

- Weakness is added.
- Fever remains present.
- Fever duration remains intact.
- Next question is selected based on the complete patient context.

## Test E: Answered question

Patient:

"My fever has lasted three days."

Expected:

- No later equivalent fever-duration question.

## Test F: Correction

Patient:

"Actually, my fever started five days ago."

Expected:

- Previous duration is retained in correction history.
- Current duration becomes five days.
- Other facts are unchanged.

## Test G: Negative symptom

Patient:

"I don't have vomiting."

Expected:

- Vomiting explicitly absent.
- It is not treated as an unknown field.
- No unnecessary question about vomiting.

## Test H: Complex patient message

Patient supplies several symptoms, durations, negatives, severity and medical history in one sentence.

Expected:

- Every extractable fact is saved.
- No information is lost.
- No unnecessary questions are generated.

## Test I: RAG medical assessment

Use a case within the documented knowledge-base coverage.

Expected:

- Structured query includes all relevant symptoms.
- Qdrant returns relevant passages.
- CrossEncoder reranks.
- Possible conditions are supported by actual evidence.
- Citation IDs resolve correctly.
- Explanation refers to actual patient facts.

## Test J: Knowledge-base gap

Use a symptom combination that is not adequately covered by the actual corpus.

Expected:

- System acknowledges missing evidence.
- Does not invent a condition.
- Does not claim successful evidence grounding.
- Does not manufacture citations.

## Test K: Emergency

Use an approved emergency test fixture.

Expected:

- Safety escalation takes priority.
- No normal questioning.
- No ordinary diagnosis generation.
- No low-risk downgrade.

## Test L: Persistence

- Restart backend.
- Resume the same session.
- Verify all symptoms, messages, corrections, summaries and question history.
- Continue the conversation without restarting intake.

## Test M: Post-assessment actions

- Ayurvedic guidance action invokes the correct evidence retrieval.
- Clinic search invokes the real OSM service.
- Google Maps links open the correct search.
- Correct condition ID is preserved.

## Test N: Multi-user isolation

Two independent users must never share case state or messages.

---

# 16. IMPLEMENTATION REQUIREMENTS

Make the actual source-code changes.

Do not merely write documentation.

Before implementing:

1. Identify the exact execution-path bug.
2. Identify every affected module.
3. Determine why existing fixes did not take effect.
4. Establish a baseline test.
5. Prepare a short implementation plan.

Then fix the actual running application.

Do not:

- Add another huge universal system prompt.
- Add unnecessary autonomous agents.
- Hardcode medical questions.
- Hardcode disease lists in prompts.
- Invent clinical probabilities.
- Invent citations.
- Use the entire transcript in every prompt.
- Replace the working RAG system.
- Introduce paid models or APIs.
- Redesign the frontend.
- Break Phase 1 persistence.
- Return fake LOW RISK classifications.
- Claim clinical validation without evidence.

Use the current official documentation for the installed versions:

- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph memory: https://docs.langchain.com/oss/python/langgraph/add-memory
- ChatGroq structured output: https://reference.langchain.com/python/langchain-groq/chat_models/ChatGroq/with_structured_output
- Qdrant query API: https://api.qdrant.tech/api-reference/search/query-points/

Verify compatibility with actual installed dependencies before modifying implementations.

---

# 17. DELIVERABLES

Create:

`BLUCARE_UNIFIED_INTELLIGENCE_IMPLEMENTATION.md`

Document:

1. Verified root cause.
2. Complete actual architecture.
3. Centralized system prompts.
4. Patient context and memory.
5. Message interpretation.
6. Symptom normalization.
7. Adaptive question planning.
8. RAG integration.
9. Medical corpus coverage.
10. Differential assessment.
11. Citation integrity.
12. General and conventional care.
13. Ayurvedic evidence integration.
14. Facilities action integration.
15. Token usage.
16. Frontend API changes.
17. Regression tests.
18. Test results.
19. Remaining limitations.

Provide actual source-code changes, automated tests and the final execution summary.

The execution summary must show actual passing and failing tests, not optimistic claims.

---

# 18. FINAL SUCCESS CRITERIA

The system is complete only when the following experience works through the actual frontend and backend.

Patient:

"Hi."

BluCare+ greets the user naturally without a risk classification.

Patient:

"I have weakness from last two days."

BluCare+ understands:

- Weakness is present.
- Duration is two days.
- No need to ask for duration again.

Patient:

"I also have fever and headache."

BluCare+ adds both symptoms and preserves weakness and its duration.

The system checks relevant medical evidence and identifies what additional information is genuinely needed.

It asks one meaningful follow-up question, not a fixed questionnaire.

The patient answers.

BluCare+ updates its complete patient context and does not forget anything.

When sufficient information is available:

- It retrieves relevant medical references.
- It reranks the evidence.
- It identifies supported possible conditions.
- It explains why each condition may fit.
- It explains uncertainty and conflicting findings.
- It provides appropriate general and conventional care information.
- It provides safe Ayurvedic information when supported.
- It displays genuine citations.
- It offers Ayurvedic guidance and nearby clinic discovery as functional actions.
- It preserves the assessment in PostgreSQL.

If evidence is insufficient, the system admits it.

If emergency signs are detected, immediate emergency guidance takes precedence.

**The final requirement is not that the graph executes or that the LLM returns valid JSON. The final requirement is that BluCare+ genuinely understands and remembers the patient, reasons over retrieved medical evidence and responds correctly across the complete consultation.**

Implement, run the exact regression scenarios, verify the actual frontend API path, document all changes and stop for review.