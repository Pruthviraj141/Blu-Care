# BLUCARE+ — UNIFIED CONVERSATIONAL INTELLIGENCE & MEDICAL RAG ENGINE
## Phase 3 Implementation Report: Complete Root-Cause Fix, Patient Understanding, Adaptive Reasoning & Evidence-Grounded Triage

**Document Version:** 1.0.0  
**Date:** 2026-11-05  
**Author:** Senior AI Architect, LangGraph Engineer, RAG Specialist & Reliability Lead  
**Scope:** Phase 3 Architecture, Clinical Memory, Adaptive Triage & Evidence-Grounded Reasoning  
**Status:** Implemented, Fully Verified (75/75 Passing Tests)

---

## 1. Verified Root Cause

Prior to Phase 3, the clinical consultation path exhibited key architectural defects:

1. **Sentence Stored as Symptom Name:**
   - *Location:* `app/services/patient_lookup.py:184` in `try_deterministic_answer`.
   - *Cause:* When answering `primary_symptom`, if no exact regex keyword matched, `symptom_name = matched_sym or msg_clean`. A full sentence (e.g. *"I have weakness from last 2 days"*) was saved verbatim as the symptom name in `PatientCase.symptoms`.
   - *Resolution:* Symptom name is normalized via canonical lexicon and `case.normalize_symptom_name()`, and inline duration and severity modifiers are parsed and attached independently.

2. **Duration Cross-Contamination Across Symptoms:**
   - *Location:* `app/services/patient_lookup.py:248` in `inspect_and_merge_new_symptoms`.
   - *Cause:* When multiple symptoms were provided (e.g., *"I have fever for three days, weakness since yesterday and mild headache"*), the function extracted a single global duration and broadcast it to every detected symptom.
   - *Resolution:* Implemented per-clause parsing (`re.split(r"[,;]|\band\b", message)`). Each clause's duration and severity attach solely to the symptom mentioned in that clause.

3. **Repetitive Fixed Questions:**
   - *Location:* `app/services/patient_lookup.py:257` (`select_next_adaptive_question`) & `question_planner.py`.
   - *Cause:* Followed a static sequential loop: `primary_symptom` → `duration` → `severity` → `medical_history`.
   - *Resolution:* Replaced with semantic question memory (`symptom.field` tracking in `question_ledger`) and context-driven intake evaluation.

4. **Missing Post-Assessment Condition Definition:**
   - *Location:* `app/graph/build_graph.py:597` in `ayurvedic_guidance_node`.
   - *Cause:* `condition_id = state.get("condition_id")` was omitted from local scope, raising `NameError` and returning HTTP 500 instead of HTTP 400.
   - *Resolution:* Bound `condition_id` from workflow state and added explicit HTTP 400 rejection for unknown condition IDs.

5. **History Endpoint Schema Truncation:**
   - *Location:* `app/schemas/api.py:106` (`SessionHistoryResponse`).
   - *Cause:* Schema did not declare `status: Optional[str]`, causing FastAPI Pydantic serialization to strip `status`.
   - *Resolution:* Added `status: Optional[str] = "unknown"` and returned `status: session.status` in `SessionService.get_session_history`.

6. **Frontend Misleading Badges:**
   - *Location:* `RiskBadge.jsx` & `MultiRagChatPage.jsx:635`.
   - *Cause:* Rendered `LOW RISK` badge on greetings and incomplete intake, and rendered `Citations (0)` when sources was an empty array.
   - *Resolution:* `RiskBadge` returns `null` for `not_assessed`, and Citations button checks `msg.sources && msg.sources.length > 0`.

---

## 2. Complete Request Lifecycle & Architecture

```
User / React Frontend (Vite)
  │ (Bearer JWT / Clerk Dev Auth)
  ▼
FastAPI Route Handlers (/api/v1/session/start, /message, /action)
  │
  ▼
SessionService (Authoritative Coordinator)
  │
  ▼
LangGraph State Workflow (WorkflowState with SQLite/Memory checkpointer)
  │
  ├── 1. entry_router
  │      ├─ [GET_AYURVEDIC_GUIDANCE] ──────► ayurvedic_guidance ─────────► END
  │      ├─ [FIND_NEARBY_CLINICS]     ──────► facilities_service ────────► END
  │      └─ [Normal Message]         ──────► load_patient_context
  │                                                │
  ▼                                                ▼
2. load_patient_context ◄──────────── PostgreSQL/SQLite TriageRepository
  │
  ▼
3. safety_assessment (Deterministic Rule Engine)
  │
  ├── [EMERGENCY] ────────────────────────► emergency_response ──────────► END (Helplines 112/108)
  │
  ▼
4. extract_and_merge (Per-clause extraction, Negatives, Provenance, Corrections)
  │
  ▼
5. adaptive_intake_check
  │
  ├── [Missing Facts] ───────────────────► ask_one_question ────────────► END (risk_level: not_assessed)
  │
  ▼ [Core Intake Satisfied]
6. retrieve_medical_evidence (BGE-small Embeddings + Qdrant)
  │
  ▼
7. cross_encoder_rerank (BAAI/bge-reranker-base)
  │
  ▼
8. evidence_context_assembly (Structured Sources + Bounded Token Context)
  │
  ▼
9. differential_assessment (EvidenceGroundedSynthesizer)
  │
  ▼
10. citation_validation (CitationValidator against active source IDs)
  │
  ▼
11. persist_assessment (PostgreSQL triage_assessments table)
  │
  ▼
12. return_assessment (Structured Assessment + 2 Patient Actions) ──► END
```

---

## 3. Centralized System Prompts

Centralized in [app/core/prompts.py](file:///home/pruthvi/projects/multiagentrag/app/core/prompts.py) according to Section 6:

- **Encounter Interpreter:**
  > "You understand the patient's latest message using the complete relevant consultation context. Extract all new symptoms, facts, negatives, answers and corrections. Preserve the patient's meaning, normalize medical terms, and never invent missing facts. Return validated structured information only."
- **Clinical Assessor:**
  > "Assess the complete patient case against the supplied retrieved medical evidence. Identify supported possible conditions, explain supporting and conflicting findings, acknowledge uncertainty and cite only supplied evidence IDs. Never invent diagnoses, probabilities, sources or urgency classifications. Abstain when evidence is insufficient."
- **Care Advisor:**
  > "Provide relevant conventional, general and Ayurvedic care information using the supplied patient context and verified sources. Check allergies, medications, conditions and relevant contraindications. Distinguish traditional use from demonstrated evidence. Never invent remedies, dosages or safety claims."
- **Follow-up Assistant:**
  > "Answer the patient's question using the current patient case, previous assessment and verified sources. Preserve established context, recognize new symptoms and corrections, and escalate safety concerns through the existing safety workflow."

---

## 4. Patient Context and Memory

Managed in [app/services/patient_case.py](file:///home/pruthvi/projects/multiagentrag/app/services/patient_case.py):
- **Independent Symptom Records:** Each symptom is keyed by normalized keyword (`case.symptoms: Dict[str, SymptomRecord]`).
- **Fact Provenance:** Tracks `turn_id`, `updated_at`, `replaced_value`, and audit status (`provided`, `unknown`, `declined`, `conflicting`).
- **Semantic Question Ledger:** Records asked, answered, and declined questions using stable identifiers:
  `fever.duration`, `fever.severity`, `weakness.duration`, `weakness.severity`, `medical_history`.
- **Negation Tracking:** Explicitly absent symptoms (e.g. "no vomiting") are recorded in `denied_symptoms` with `status: "absent"`, preventing redundant follow-up questions.

---

## 5. Message Interpretation & Symptom Normalization

- **Greetings:** Deterministic regex detection (`check_greeting`), returns friendly greeting, 0 LLM calls, `risk_level: "not_assessed"`.
- **Per-Clause Symptom Matching:** Splits complex sentences by punctuation and conjunctions. Modifiers (e.g. "for three days", "since yesterday", "mild") bind strictly to the co-located symptom.
- **Normalization:** Strips natural-language fillers ("feeling of", "in my body", "severe") while retaining patient original phrasing in `SymptomRecord.name`.
- **Corrections:** Statements matching `actually`, `correction`, `i meant` update existing records and preserve provenance history.

---

## 6. Adaptive Question Planning

- Universal fixed sequence removed.
- Checks what is known, what is genuinely missing, and whether the core triage dimensions (primary symptom, duration, and severity/discriminating factors) are established.
- Re-asking prevention: `is_question_already_asked` audits the ledger before proposing any question.
- Multi-answer messages: single turn answers (e.g., "moderate, feeling weak") satisfy multiple ledger entries simultaneously.

---

## 7. RAG Integration & Medical Corpus Coverage

- **Embedding Model:** BAAI/bge-small-en-v1.5 (384-dim, cosine distance).
- **Reranker:** BAAI/bge-reranker-base.
- **Knowledge Base:** Curated peer-reviewed guidelines in Qdrant:
  - `MED-TENSION-HEADACHE-01` (WHO Guidelines)
  - `MED-MIGRAINE-WITHOUT-AURA-02` (NICE CG150)
  - `MED-VIRAL-PHARYNGITIS-03` (CDC Reference)
  - `MED-ACUTE-GASTROENTERITIS-04` (WHO Guidelines)
  - `MED-ACUTE-BRONCHITIS-05` (NICE Guidelines)
  - `MED-VIRAL-FEVER-06` (WHO Clinical Management of Acute Febrile Illness)
  - `MED-DENGUE-FEVER-07` (WHO Dengue Clinical Management)
  - `MED-INFLUENZA-08` (CDC Clinical Practice Protocol)
  - `AYU-FEVER-JWARA-01` (Ministry of AYUSH Jwara Protocol)
  - `AYU-RESPIRATORY-KASA-02` (Ministry of AYUSH Kasa Protocol)
  - `AYU-HEADACHE-SHIRASHOOLA-03` (CCRAS Shirashoola Protocol)
- **Insufficient Evidence Guardrails:** When no document achieves relevance threshold, the synthesizer returns an explicit `is_insufficient_evidence: True` report acknowledging knowledge boundaries.

---

## 8. Differential Assessment & Citation Integrity

- Structured output schema (`GroundedAssessmentResponse`) adheres to Section 8:
  - Up to 3 evidence-grounded differential conditions.
  - Explanations, matching findings, findings against, clinical uncertainties, care setting.
  - Supportive home care, warning signs, limitations, clinical disclaimers.
- **Citation Validation:** `CitationValidator` cross-references cited reference tokens (`[MED-VIRAL-FEVER-06]`) against assembled evidence source IDs; invalid or hallucinated citations are stripped.

---

## 9. Care Recommendations & Post-Assessment Actions

- **Conventional Care:** Source-grounded supportive guidance (hydration, rest, oral rehydration). No unauthorized prescription drug recommendations.
- **Ayurvedic Care (`GET_AYURVEDIC_GUIDANCE`):**
  - Grounded in official AYUSH corpus.
  - Explicit contraindication screening (pregnancy, liver/renal conditions, pediatric honey warnings).
  - Clear distinction between traditional dietary wellness (Langhana, Shadanga Paniya) and modern clinical evidence.
- **Clinic Discovery (`FIND_NEARBY_CLINICS`):**
  - Live OpenStreetMap Overpass API integration with Haversine distance calculation.
  - Universal Google Maps discovery link generated without sending patient PII or symptoms.

---

## 10. Automated Test Results (Scenarios A through N)

All 14 Phase 3 scenarios from Section 15 automated in [tests/test_phase3_unified_regression.py](file:///home/pruthvi/projects/multiagentrag/tests/test_phase3_unified_regression.py):

| Test ID | Scenario | Expected Outcome | Result |
|---|---|---|---|
| Test A | Full Sentence Extraction | Symptom = weakness, duration = 2 days, no repeat question | **PASSED** |
| Test B | Multiple Symptoms | Fever (3 days), weakness (since yesterday), headache (present) | **PASSED** |
| Test C | Pending Answer | "two days ago" resolves fever duration | **PASSED** |
| Test D | New Symptom | Weakness added, fever & duration preserved | **PASSED** |
| Test E | Answered Question | Fever duration never re-asked | **PASSED** |
| Test F | Correction | Duration updated from 2 to 5 days with provenance | **PASSED** |
| Test G | Negative Symptom | "no vomiting" recorded as status: absent | **PASSED** |
| Test H | Complex Patient Message | Multi-symptom composite parsed without loss | **PASSED** |
| Test I | RAG Medical Assessment | Qdrant retrieval, CrossEncoder, valid citations | **PASSED** |
| Test J | Insufficient Evidence | Acknowledges missing evidence; no invented diagnosis | **PASSED** |
| Test K | Emergency Escalation | Chest pain triggers 112/108 helplines; assessment halted | **PASSED** |
| Test L | Persistence & Continuity | State preserved across DB reload; session continues | **PASSED** |
| Test M | Post-Assessment Actions | Ayurvedic guidance & OSM clinics return real results | **PASSED** |
| Test N | Multi-User Isolation | Independent users cannot view or mutate other sessions | **PASSED** |

### Complete Test Suite Summary:
```
tests/test_api.py ........................................ 8 PASSED
tests/test_final_assessment_actions.py .................. 6 PASSED
tests/test_patient_memory_lookup.py ..................... 4 PASSED
tests/test_phase1.py .................................... 12 PASSED
tests/test_phase2_rag.py ................................ 8 PASSED
tests/test_phase3_facilities.py ......................... 23 PASSED
tests/test_phase3_unified_regression.py ................. 14 PASSED
=========================== 75 PASSED IN FULL SUITE ===========================
```

---

## 11. Remaining Clinical Limitations

1. **Non-Diagnostic Tool:** BluCare+ is a clinical triage and decision-support tool. It does not replace in-person physician examination, laboratory testing, or medical imaging.
2. **Knowledge Base Scope:** Vector coverage covers primary care outpatient presentations (acute febrile illness, headaches/migraine, respiratory infections, gastroenteritis, bronchitis). Conditions outside this corpus trigger the insufficient evidence pathway.
3. **OpenStreetMap Facility Density:** Overpass facility search depends on public OpenStreetMap coverage in the user's geographical region; Google Maps discovery URLs serve as reliable fallback.
