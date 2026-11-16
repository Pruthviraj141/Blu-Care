# BLUCARE+ — INTELLIGENT CONVERSATION, CLINICAL REASONING & REAL-TIME FACILITY DISCOVERY
## Complete Final Engineering Improvement

**Role:** Senior AI Architect, LangGraph Engineer, RAG Engineer, Clinical Decision-Support Software Engineer and Full-Stack Backend Engineer.

**Objective:** Transform BluCare+ into a genuinely conversational symptom-triage system that understands patients from beginning to end, asks intelligent symptom-specific follow-up questions, reasons over medical evidence and provides useful next steps.

This is not a SaaS platform. Keep the architecture simple, focused and maintainable.

Do not build another application or add unnecessary agents.

Do not redesign the existing UI.

Preserve all working Phase 1, Phase 2 and Phase 3 functionality.

---

# 1. ROOT PROBLEMS TO FIX

The current system:

- Ends intake too early.
- Asks generic questions instead of condition-specific questions.
- Treats subjective severity as sufficient clinical information.
- Sometimes assumes unreported symptoms are absent.
- Generates an acute viral fever conclusion too quickly.
- Does not sufficiently use RAG to guide additional questioning.
- Returns generic warnings.
- Sometimes fails to return nearby facilities.
- Does not reliably distinguish unassessed risk from an assessed triage category.

Inspect the real execution path and fix these behaviours in the actual running application.

Do not merely modify the system prompts.

---

# 2. ONE SHARED UNDERSTANDING OF THE PATIENT

Use the existing LangGraph persistent thread and PostgreSQL patient-case state.

Every turn must receive the latest complete relevant patient context.

Maintain:

- Chief complaint.
- All symptoms.
- Original patient wording.
- Normalized medical terms.
- Individual onset and duration.
- Severity.
- Progression.
- Frequency.
- Triggers.
- Relieving factors.
- Explicitly absent symptoms.
- Unknown symptoms.
- Medical history.
- Current medications.
- Allergies.
- Relevant risk factors.
- Previously answered questions.
- Pending questions.
- Encounter summary.
- Safety outcomes.

Each symptom must retain its individual details.

Never assign one symptom's duration to every symptom.

Never overwrite existing patient facts with an incomplete extraction.

Never store a complete sentence as a symptom name.

Never confuse unknown with absent.

Every correction must update the correct field and retain its provenance.

Use a single authoritative patient-case record.

---

# 3. REPLACE GENERIC QUESTIONING WITH INTELLIGENT CLINICAL CONVERSATION

This is the most important requirement.

The system must not follow a fixed list of questions.

It must understand:

1. What the patient is experiencing.
2. What information is already known.
3. What information remains unknown.
4. Which possible conditions are supported by current medical evidence.
5. What additional information would meaningfully distinguish those possibilities.
6. Which question should be asked next.

## Dynamic questioning

Use the complete patient case and retrieved medical evidence to determine the next question.

Ask multiple related follow-up questions naturally when useful, but do not overwhelm the patient.

For example:

A patient reporting fever for two days may need clarification about:

- Actual measured temperature and measurement method.
- Chills or body aches.
- Headache or neck symptoms.
- Cough, sore throat or breathing symptoms.
- Vomiting, diarrhea or abdominal symptoms.
- Rash or urinary symptoms.
- Hydration and urine output.
- Relevant recent travel, mosquito exposure or sick contacts.
- Age and relevant medical risk factors.

These are examples of possible information gaps, not a fixed questionnaire.

Ask only what is relevant to the patient's actual symptoms and the evidence-supported differential.

A case of generalized weakness requires different clarification from focal or one-sided weakness.

## Question depth

Do not stop questioning merely because primary symptom, duration and subjective severity are known.

For non-emergency cases, aim to gather enough useful clinical context, often across approximately 3–5 targeted information areas when necessary.

This is not a mandatory minimum or fixed number.

Some cases need fewer questions; others need additional clarification.

Each response can contain one focused question or a small, naturally grouped set of closely related questions.

Never repeat answered questions.

Never ask for information already provided in the original sentence.

Never ask irrelevant questions just to reach a question count.

## Evidence-driven questions

Use retrieved medical references to identify which findings distinguish supported conditions.

For example, do not ask "Have you travelled anywhere?" for every fever patient.

Ask about travel, exposure or mosquito bites only when the patient context, local epidemiology or retrieved evidence makes that information relevant.

The question planner must explain internally which missing fact justifies each question.

---

# 4. MAKE RAG PART OF THE REASONING PROCESS

RAG must not be a final optional lookup.

It must support understanding and differentiation of possible conditions.

Use the existing:

BGE → Qdrant → CrossEncoder → Evidence Context.

## Preliminary evidence search

After understanding a clinically meaningful initial complaint:

1. Build a query from the structured patient case.
2. Retrieve relevant medical passages.
3. Rerank them.
4. Identify evidence-supported candidate conditions.
5. Identify clinically important differences between candidates.
6. Determine which unknown patient facts could change the assessment.
7. Use those facts to guide the next questions.

Do not perform unnecessary retrieval for greetings or unchanged simple answers.

Reuse evidence when the structured case and retrieval configuration remain unchanged.

## Final evidence retrieval

After intake:

1. Rebuild the query from the latest complete case.
2. Perform fresh retrieval when necessary.
3. Rerank the candidates.
4. Preserve genuine source metadata.
5. Generate the assessment from the final evidence context.
6. Validate citations.

Do not use the embedding similarity or CrossEncoder score as disease probability.

Do not hardcode disease names inside system prompts.

Only identify conditions supported by the actual medical corpus.

---

# 5. FEVER CASE — REQUIRED DEMONSTRATION

The current system incorrectly jumps to acute viral fever after collecting only duration and subjective severity.

Use this test:

Patient: "I have fever."

Assistant: Ask about onset/duration and measured temperature if not supplied.

Patient: "For two days."

Assistant: Ask for an actual temperature reading if available, rather than assuming that mild/moderate/severe describes an objective temperature.

Patient: "It's mild."

Assistant: Explore relevant associated symptoms in a natural question. For example, ask whether there are chills, body aches, headache, cough, sore throat, stomach symptoms, rash or urinary discomfort.

Patient answers.

Assistant: Update every applicable symptom and ask only the next clinically relevant question.

Further questioning should depend on the information supplied.

Potential information gaps may include:

- Whether symptoms are improving or worsening.
- Hydration and ability to drink.
- Significant associated symptoms.
- Relevant medical conditions.
- Medication or allergy information when needed.
- Relevant exposures or travel.
- Red-flag symptoms.

Do not ask all these automatically.

The system must distinguish:

- Fever reported.
- Fever objectively measured.
- Subjective severity.
- Associated symptoms.
- Symptoms explicitly absent.
- Unknown information.

Only after gathering sufficient relevant context should the final assessment be produced.

Do not assume that a two-day mild fever is necessarily viral.

Compare the complete case against actual retrieved references.

If the corpus cannot distinguish possible causes, explicitly acknowledge that limitation.

---

# 6. FINAL DIFFERENTIAL ASSESSMENT

Generate a structured assessment using the complete case and final retrieved evidence.

Include:

- Concise patient-case summary.
- Up to three supported possible conditions.
- Why each condition may fit.
- Supporting findings.
- Findings against each possibility.
- Remaining uncertainties.
- Recommended care setting where supported by approved clinical rules.
- General care.
- Evidence-supported conventional information.
- Relevant warning signs.
- Genuine medical sources.
- Evidence limitations.

Do not force three conditions.

Do not invent diagnostic percentages.

Do not give a definitive diagnosis.

Never claim that unreported symptoms are absent.

Never return generic care advice as a substitute for differential analysis when relevant evidence exists.

If evidence is insufficient, abstain.

---

# 7. ADAPTIVE CARE RECOMMENDATIONS

Support three clearly distinguished categories:

### General care
Relevant supportive information grounded in appropriate references.

### Conventional medical information
General information about appropriate medical evaluation and supported OTC options.

No personalized prescriptions, invented dosages or unsupported drug recommendations.

### Ayurvedic and complementary information
Retrieve genuine relevant Ayurvedic evidence separately.

Consider patient allergies, medications, conditions, pregnancy where relevant and contraindications.

Distinguish traditional use from demonstrated clinical effectiveness.

Never invent herbs, formulations or dosages.

Never recommend unverified potentially toxic preparations or replacing necessary conventional care.

When evidence is inadequate, explicitly abstain.

These recommendations must use the same patient context, not a newly created conversation.

---

# 8. REAL NEARBY CLINIC AND HOSPITAL DISCOVERY

The current output says no clinics exist within 5 km of Sukhsagar Nagar, Pune.

This requires an actual integration investigation.

A current local-directory search identifies facilities in that area, including Siddhivinayak Hospital, Prerna Hospital, Dr. Khabiya's Clinic, Purohit Clinic and other local practices.

Do not add these manually as hardcoded production hospital data.

## 8.1 Exact reproducible test area

Use:

```text
Area: Sukhsagar Nagar, Katraj, Pune
Latitude: 18.456229
Longitude: 73.8710766
Initial radius: 5000 metres
Expanded test radius: 10000 metres
```

These are test coordinates, not a production user location.

## 8.2 Verify Overpass directly

Before modifying the facilities code, execute a real HTTP request using the configured Overpass endpoint.

Search:

- `amenity=hospital`
- `amenity=clinic`
- `amenity=doctors`
- `healthcare=hospital`
- `healthcare=clinic`
- `healthcare=doctor`
- Other relevant mapped healthcare tags supported by the current tagging schema.

Search:

- Nodes.
- Ways.
- Relations.

Parse center coordinates for area features.

Check the actual response for Sukhsagar Nagar at 5 km and 10 km.

Record:

- HTTP status.
- Query duration.
- Number of returned elements.
- Facility names.
- OSM types and IDs.
- Available tags.
- OSM database timestamp.
- Parsing failures.

Do not substitute mocked HTTP responses for the live integration test.

If no facilities are returned, investigate query construction, supported tags, coverage and radius before declaring that no facilities exist.

## 8.3 Improve the real-time location flow

Use actual browser geolocation.

The frontend should request permission using the supported browser Geolocation API.

Requirements:

- Use the coordinates supplied by the browser.
- Do not hardcode Pune or Nashik.
- Do not infer coordinates from IP addresses.
- Pass validated latitude and longitude to FastAPI.
- Handle permission denied.
- Handle unavailable GPS.
- Handle location timeout.
- Display which location was used.
- Allow location retry.

The backend must never silently substitute an old location.

## 8.4 Improve facilities search

Keep the free integration:

OpenStreetMap + Overpass + Haversine + Google Maps Search URLs.

Requirements:

- Search for both hospitals and clinics.
- Include common alternate healthcare tags.
- Deduplicate nodes, ways and relations.
- Calculate straight-line distance.
- Sort by actual distance.
- Return available addresses and phone numbers only.
- Preserve OSM attribution.
- Report the actual search radius.
- Cache responsibly.
- Respect shared Overpass fair-use policies.

If no results exist within 5 km, optionally retry once at 10 km.

Never state that no hospital exists when only the OSM query returned zero results.

## 8.5 Google Maps search fallback

Always generate the official Google Maps Search URL when valid coordinates exist.

For example:

```text
https://www.google.com/maps/search/?api=1&query=clinics+near+LAT,LNG
```

Use proper URL encoding.

This must work even if Overpass returns zero facilities or is temporarily unavailable.

Do not scrape Google Maps.

Do not claim Google Maps results are structured backend records.

Do not introduce Google Places API or billing.

## 8.6 Pune acceptance test

The exact Sukhsagar test must demonstrate:

1. Correct test coordinates are used.
2. 5 km Overpass query executes.
3. 10 km fallback behaves correctly.
4. Actual OSM records are parsed where present.
5. Distance calculations are correct.
6. Google Maps hospital search URL is returned.
7. Google Maps clinic search URL is returned.
8. Zero OSM results do not mean zero real-world facilities.
9. The actual browser location works separately from the Pune test override.

Also test a second location from the browser's real location permission.

Do not pass this test using hardcoded local hospital results.

---

# 9. SIMPLIFIED LANGGRAPH ARCHITECTURE

Maintain one understandable graph:

```text
START
  |
  v
Load Patient Context
  |
  v
Interpret Latest Message
  |
  v
Merge Patient Facts
  |
  v
Safety Assessment
  |
  +---- Emergency ---> Immediate Guidance
  |
  v
Evidence Retrieval
  |
  v
Clinical Information Gap Analysis
  |
  +---- Relevant Question Needed
  |              |
  |              v
  |       Ask Contextual Question
  |              |
  |             END
  |
  v
Final Evidence Retrieval
  |
  v
Differential Assessment
  |
  v
Citation Validation
  |
  v
Care Recommendations
  |
  v
Persist Assessment
  |
  v
END
```

Post-assessment actions:

- Ayurvedic evidence retrieval.
- Nearby hospital and clinic lookup.
- Follow-up questions about the assessment.

Do not introduce a separate autonomous agent for every operation.

Use Python for deterministic state updates, safety, persistence and question deduplication.

Use the existing Groq model for meaningful natural-language interpretation and medical synthesis.

---

# 10. TOKEN AND CONTEXT EFFICIENCY

Do not fix conversational quality by repeatedly sending enormous prompts and full transcripts.

- Greetings: zero LLM calls.
- Simple known answers: deterministic parsing where reliable.
- Complex messages: one structured interpretation call.
- Patient-state merging: Python.
- Safety rules: Python.
- Evidence retrieval: reuse cached results when valid.
- Question planning: use compact current patient context and relevant evidence.
- Final synthesis: one structured assessment call.

Keep system prompts short.

Do not summarize on every turn.

Use the full persistent patient context and a concise encounter summary.

Track actual Groq usage and stage latency.

Do not compromise clinical understanding simply to hit a rigid token target.

---

# 11. REMOVE MISLEADING FRONTEND OUTPUT

Do not redesign the UI.

Correct only functional presentation problems:

- Never display LOW RISK while the assessment is unassessed.
- Never display retrieval similarity as an 85% disease match.
- Do not display empty citations.
- Do not claim no hospitals exist when OSM returns zero records.
- Clearly distinguish OSM records from external Google Maps search.
- Display the actual location and radius used.

---

# 12. MANDATORY END-TO-END REGRESSION TESTS

Test the actual frontend-to-backend path.

### Conversation test

Patient:

"I have weakness from last two days."

Expected:

- Weakness extracted.
- Duration two days.
- No redundant duration question.

Patient:

"I also have fever and headache."

Expected:

- Both symptoms added.
- Previous weakness retained.
- Individual durations handled correctly.

Patient answers relevant follow-up questions.

Expected:

- No repeated questions.
- Questions adapt to the current case.
- No premature diagnosis.

### Fever reasoning test

Use the complete fever interaction described above.

Expected:

- More clinically relevant information gathered where needed.
- Associated symptoms accurately recorded.
- No invented negative symptoms.
- Evidence-supported differential.
- Honest uncertainty.
- Correct sources.

### Facilities test

Test the exact Sukhsagar coordinates and a real browser-provided location.

Expected:

- Real Overpass query.
- Correct results where mapped.
- Google Maps links even if OSM results are empty.
- No fabricated hospital list.

### Ayurvedic test

Select a supported condition and request Ayurvedic guidance.

Expected:

- Genuine relevant sources.
- Safety checking.
- Appropriate abstention when evidence is insufficient.

### Emergency test

Emergency safety always interrupts normal intake and assessment.

### Persistence test

Restart the backend and resume the existing session.

All facts, messages, question history and assessments must remain correct.

---

# 13. DELIVERABLES

Implement the actual code changes.

Create:

`BLUCARE_CONVERSATIONAL_CLINICAL_REASONING_REPORT.md`

Include:

1. Root causes.
2. Conversation architecture.
3. Adaptive questioning design.
4. Patient memory.
5. RAG-driven question selection.
6. Final differential assessment.
7. Care recommendation architecture.
8. Pune Overpass live test.
9. Browser geolocation verification.
10. Facilities improvements.
11. Token measurements.
12. Actual test results.
13. Remaining limitations.

Report the real HTTP responses and exact test counts.

Never claim a live location integration worked if only mock coordinates were used.

Never claim clinical validation based solely on automated tests.

# 14. STRICT RULES

- No new paid APIs.
- No Google Places.
- No Google Maps scraping.
- No hardcoded diseases.
- No generic fixed questionnaire.
- No repeated questions.
- No fabricated citations.
- No fake hospital results.
- No fake confidence percentages.
- No unnecessary agents.
- No giant system prompts.
- No frontend redesign.
- No destruction of existing RAG or patient memory.
- No fabricated clinical advice.

Preserve working application features.

Fix the actual running code and prove the result using real API requests.

**FINAL SUCCESS CONDITION**

BluCare+ must behave like an intelligent conversational symptom-triage assistant.

It must understand the patient's entire consultation, ask relevant condition-specific questions, use real retrieved medical evidence to compare possible conditions, explain uncertainty, provide safe care guidance, and find nearby real medical facilities using the user's actual location.

Complete implementation, tests and documentation. Stop for review.