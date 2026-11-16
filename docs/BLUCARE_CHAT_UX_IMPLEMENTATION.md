# BluCare+ — Conversational Chat & Structured Medical Assessment UI Implementation

**Design System:** Linear + Apple Notes (minimal, precise, clinical, and highly readable).  
**Objective:** Transform BluCare+ from a basic markdown-dump chatbot into a polished, genuinely conversational medical-triage workspace with progressive structured assessment cards, collapsible clinical accordions, dual-care action bars, verified OpenStreetMap facility cards, and zero-PII Google Maps integration.

---

## 1. Executive Summary

Previously, the BluCare+ triage chat rendered all assistant responses—including full differential assessments—as a single monolithic Markdown string via `<ReactMarkdown>{msg.text}</ReactMarkdown>`. The rich clinical state computed by LangGraph (symptom facts, differential conditions with rationale, conflicting evidence, remaining uncertainties, warning signs, citations, and post-assessment care actions) was flattened and lost.

This implementation delivers:
1. **Linear + Apple Notes UI/UX Design System**: Restrained typography, subtle borders (`rgba(255,255,255,0.07)` / `0.14`), 4px base spacing increments, clinical teal (`#14B8A6`) and cyan (`#0EA5E9`) accents, eliminating bulbous SaaS glow and neon badges.
2. **Modular Component Architecture**: 12 dedicated, accessible components under `frontend/src/components/chat/`.
3. **Structured Assessment Card**: Displays clinical header, urgency status (only when assessed), normalized reported symptoms, individual condition cards with <200ms accessible disclosures, grouped care recommendations, and medical source citations.
4. **Emergency Safety Disclosure**: If an assessment detects an emergency or high risk, the critical notice and SOS emergency action remain **immediately visible** and are strictly never hidden inside a collapsible accordion.
5. **Real Progressive Response Rendering**: Non-blocking typing indicator with step status, assessment skeleton progress states ("Understanding symptoms", "Reviewing clinical guidelines", "Synthesizing differential assessment"), and cancellation/pause control (`handleStopGeneration`).
6. **Two Aligned Care Actions**: Visually aligned action bar for **Ayurvedic Complementary Guidance** (secondary action, leaf icon, idempotent execution) and **Find Nearby Clinics** (primary action, browser geolocation with fallback, Overpass OSM facilities search).
7. **Verified Facility Cards**: Displays distance, address, contact numbers with `tel:` links, direct OSM directions, and zero-PII Google Maps search URLs (`https://www.google.com/maps/search/?api=1&query=...`).

---

## 2. Component Architecture & Hierarchy

```
frontend/src/components/chat/
├── ChatMessage.jsx              # Master chat message container (User vs Assistant)
├── TypingIndicator.jsx          # Subtle 3-dot pulse with status text and stop control
├── StreamingMessage.jsx         # Conversational markdown container with blinking cursor
├── AssessmentCard.jsx           # Master clinical assessment container
├── AssessmentSummary.jsx        # Normalized reported present & denied symptoms
├── ConditionCard.jsx            # Individual condition card with collapsible clinical analysis
├── RecommendationSection.jsx    # Grouped care recommendations (General, Conventional, Ayurvedic)
├── WarningAccordion.jsx         # Non-collapsible emergency notice + collapsible warning signs
├── SourceAccordion.jsx          # Collapsible clinical evidence & citations
├── CareActionBar.jsx            # Aligned Dual Care Action Bar (Ayurvedic + Nearby Clinics)
├── FacilityCard.jsx             # Facility card with direct directions & Google Maps action
└── AssessmentSkeleton.jsx       # Clinical skeleton with progress indicator
```

### Hierarchy Inside `ChatMessage.jsx`

```
ChatMessage
├── [Role = User] -> User Bubble (Linear minimal card)
└── [Role = Assistant] ->
    ├── [Assessment Present] -> AssessmentCard
    │   ├── AssessmentHeader & Urgency Badge (Clinical Assessment, date/time)
    │   ├── AssessmentSummary (Present symptoms with duration/severity, denied symptoms)
    │   ├── ConditionCards (Name, short explanation, collapsible clinical rationale/findings)
    │   ├── WarningAccordion (Persistent Emergency Banner if high risk + collapsible warning list)
    │   ├── RecommendationSection (General supportive, Conventional medical, Ayurvedic)
    │   ├── SourceAccordion (Numbered clinical citations with titles, publishers, links)
    │   └── CareActionBar (Aligned Ayurvedic guidance + Nearby clinics)
    ├── [Facilities Present] -> FacilityCards Grid
    │   └── FacilityCard (Category, distance, address, phone tel: link, OSM directions, Google Maps search)
    └── [Conversational Turn] -> Restrained Markdown Body with copy action
```

---

## 3. Design System & Style Tokens

Implemented in `frontend/src/index.css`:

```css
:root {
  --bg-app: #0B0D0E;
  --bg-subtle: #121517;
  --bg-surface: #181C1E;
  --bg-elevated: #202528;

  --text-primary: #F0F3F5;
  --text-secondary: #9BA3A9;
  --text-muted: #6B747B;

  --border-subtle: rgba(255, 255, 255, 0.07);
  --border-strong: rgba(255, 255, 255, 0.14);

  --clinical-teal: #14B8A6;
  --clinical-cyan: #0EA5E9;

  --severity-emergency: #EF4444;
  --severity-urgent: #F59E0B;
  --severity-routine: #10B981;
  --severity-selfcare: #06B6D4;
}
```

- **Radii**: 6px for controls/buttons, 10px for cards, 14px for master containers.
- **Typography**: Inter base font, 14px body text, 12px metadata/badges, crisp monospace for reference IDs and timestamps.
- **Motion**: Restrained CSS transitions strictly under 200ms (`transition: all 180ms cubic-bezier(0.16, 1, 0.3, 1)`). Respects `@media (prefers-reduced-motion: reduce)`.

---

## 4. Backend Schema & Response Mapping

To ensure backward compatibility without modifying clinical reasoning or RAG retrieval contracts, the following additions were implemented:

1. **`app/schemas/api.py`**:
   - `ChatMessageResponse`, `HistoricalMessage`, and `SessionHistoryResponse` augmented with optional fields:
     - `assessment: Optional[Dict[str, Any]] = None`
     - `facilities: Optional[List[Dict[str, Any]]] = None`
     - `external_search: Optional[Dict[str, Any]] = None`
     - `ayurvedic_guidance: Optional[Dict[str, Any]] = None`
2. **`app/graph/build_graph.py`**:
   - `facilities_service_node`: Emits structured `facilities` array and `external_search` alongside markdown fallback.
   - `ayurvedic_guidance_node`: Formats structured `ayurvedic_guidance` object with remedies, diet, and lifestyle recommendations.
3. **`app/core/session_service.py`**:
   - `process_message`: Passes structured payload through to API response.
   - `get_session_history`: Attaches stored `assessment` to the latest bot message upon session reload.

---

## 5. Streaming & Progressive Rendering

- **Conversational Turns**: Standard messages stream actual text with a blinking cursor and `TypingIndicator` showing the active agent status (`Understanding symptoms`, `Analyzing clinical context`).
- **Generation Control**: Users can cancel or pause in-flight assistant requests at any time via `handleStopGeneration` using `AbortController.abort()`.
- **Structured Assessments**: In multi-agent medical evaluation, returning incomplete JSON violates clinical safety. BluCare+ uses verified multi-stage progressive skeletons during synthesis, followed by smooth section-by-section entrance animations once the validated schema arrives. Fake word-split simulated token streaming is strictly avoided.

---

## 6. Accessibility & Collapsible Disclosures

- **ARIA Compliant**: All collapsible triggers (`ConditionCard`, `WarningAccordion`, `SourceAccordion`, `RecommendationSection`) implement `aria-expanded`, `aria-controls`, and `role="region"`.
- **Keyboard Navigation**: Full keyboard support (`Space`, `Enter`, `Tab`).
- **Safety Guarantee**: Emergency warnings (`risk_level: 'emergency'` / `'high'`) are pinned to the top of the assessment card and rendered as persistent, non-collapsible alerts.

---

## 7. Dual Care Actions & Facility Discovery

- **Care Action Bar**: Visually aligned at the bottom of the assessment card.
  - Secondary Action: **Explore Ayurvedic Guidance** (🌿). Disables upon execution to prevent duplicate requests.
  - Primary Action: **Find Nearby Clinics** (🏥). Queries browser geolocation (`navigator.geolocation.getCurrentPosition`) with accurate fallback coordinates (`12.9716, 77.5946`).
- **Overpass OSM Facilities**:
  - Distance calculation using the Haversine formula.
  - Category badges (`Hospital`, `Clinic`, `Doctors`).
  - Contact links (`tel:...`) where available.
  - Direct navigation directions via OpenStreetMap.
  - Zero-PII Google Maps search action (`https://www.google.com/maps/search/?api=1&query=...`).
  - Attribution preserved: `© OpenStreetMap contributors`.

---

## 8. Verification & Test Results

1. **Frontend Production Build**:
   ```bash
   npm run build
   # Output: vite v6.4.1 building for production...
   # 2119 modules transformed.
   # dist/assets/index-DQnfp8ZE.js 492.00 kB │ gzip: 150.79 kB
   # ✓ built in 5.21s
   ```
2. **Backend Regression Tests**:
   - All backend tests in `tests/` pass with zero regressions across LangGraph, API endpoints, patient memory, and facilities services.

---

## 9. Remaining Limitations & Future Considerations

- **SSE Streaming for Long Assessments**: While conversational messages stream progressively, full differential assessments are returned as atomic validated objects to guarantee 100% schema integrity and avoid incomplete medical advice.
- **Offline Maps**: Facility discovery depends on active internet connectivity to OpenStreetMap Overpass servers. If Overpass is unreachable, graceful fallback offers direct zero-PII Google Maps search.
