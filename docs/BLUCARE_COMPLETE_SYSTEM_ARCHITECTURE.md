# BLUCARE+ — COMPLETE SYSTEM ARCHITECTURE
## End-to-End Technical Reference & Component Topologies

**Document Version:** 1.0.0  
**Architectural Scope:** Full Stack (Frontend, Backend, Vector Store, PostgreSQL, External Integrations)  
**Date:** 2026-11-04  

---

## 1. System Overview

BluCare+ is an AI-powered medical symptom-triage decision-support system. It provides structured symptom intake, dynamic follow-up questioning, real-time safety evaluation, evidence-grounded medical assessment retrieval with verified citations, and genuine nearby healthcare facility discovery.

```mermaid
graph TD
    Client["Browser / React Frontend (Vite + Clerk)"] -->|"HTTPS / Bearer JWT"| Gateway["FastAPI Application (Port 8000)"]
    Gateway -->|"Verify Token"| Clerk["Clerk Authentication Server"]
    Gateway -->|"Lifecycle / Turn"| SessionService["SessionService (app/core)"]
    
    SessionService -->|"1. Safety Check"| SafetyEngine["SafetyEngine (Red Flag Rules)"]
    SafetyEngine -->|"Emergency"| EmergencyStore["Record TriageSafetyEvent"]
    
    SessionService -->|"2. Symptom Intake"| Extractor["SymptomExtractor & PatientCase"]
    Extractor -->|"Incomplete"| QuestionPlanner["QuestionPlanner (Ask Next Question)"]
    
    Extractor -->|"Complete Intake"| RAGPipeline["Phase 2 RAG Evidence Pipeline"]
    RAGPipeline -->|"BGE Small Embedding"| VectorStore["Qdrant Vector Database"]
    VectorStore -->|"Top Passages"| Reranker["CrossEncoder BGE-Reranker"]
    Reranker -->|"Curated Passages"| LLMSynth["Groq LLM Synthesis (Qwen / GPT-OSS)"]
    LLMSynth -->|"Draft Assessment"| Validator["CitationValidator (app/rag)"]
    Validator -->|"Validated Assessment"| DBStore["Persist in PostgreSQL (triage_assessments)"]

    Gateway -->|"Nearby Facilities"| FacilitiesService["FacilitiesService (app/facilities)"]
    FacilitiesService -->|"Structured POIs"| Overpass["OpenStreetMap Overpass API"]
    FacilitiesService -->|"Haversine Distance"| DistanceCalc["Haversine Formula (Python)"]
    FacilitiesService -->|"Universal Maps URLs"| GoogleMaps["Google Maps Search URLs"]
    Gateway -->|"Emergency Numbers"| EmergencyDirectory["Government Directory (India 112, etc.)"]
```

---

## 2. Complete Request Lifecycle

### 2.1 Symptom Intake Turn Lifecycle
1. **User Authentication:** Client issues `POST /api/v1/session/message` with JSON `{ "thread_id": "...", "message": "..." }` and `Authorization: Bearer <clerk_jwt>`.
2. **Gateway Verification:** `get_current_user` validates token signature against cached Clerk JWKS or dev environment bypass.
3. **Session Retrieval & Ownership Check:** `TriageRepository.get_session` fetches the active `TriageSession` by `thread_id` and ensures `clerk_user_id` matches.
4. **Emergency Evaluation (Safety First):** `SafetyEngine.evaluate` inspects current user message and accumulated symptom history for acute red flags (e.g., crushing chest pain radiating to left arm). If matched:
   - Status changes to `emergency`.
   - `TriageSafetyEvent` is recorded in PostgreSQL.
   - Normal intake and RAG stop immediately. Emergency guidance and verified emergency contacts are returned.
5. **Structured Symptom Extraction:** `SymptomExtractor.extract` identifies primary symptom, duration, severity, and modifiers, updating `PatientCase` with fact provenance.
6. **Adaptive Question Planning:** If essential clinical triage dimensions (duration, severity) are unstated:
   - `QuestionPlanner.evaluate_intake` determines the single highest-priority missing dimension.
   - The question is returned to the user, and session status remains `intake`.
7. **RAG Pipeline Execution (Intake Complete):** When all required intake dimensions are satisfied:
   - `build_medical_query` generates a deterministic clinical retrieval query.
   - BGE embeddings query Qdrant; top candidates are reranked via `CrossEncoder`.
   - `assemble_medical_context` builds verified source context.
   - `EvidenceGroundedSynthesizer` generates clinical explanations with `[EVID-XXX]` citations.
   - `CitationValidator` strips any hallucinated citations, ensuring 100% citation grounding.
8. **Assessment Persistence:** `TriageRepository.save_assessment` writes the structured assessment to `triage_assessments` in PostgreSQL.
9. **API Response:** Clean, formatted triage recommendations, warning signs, and validated sources are returned.

---

## 3. Facilities Discovery Architecture

Facilities search is completely decoupled from symptom intake and clinical reasoning:

```mermaid
sequenceDiagram
    autonumber
    actor User as Patient / User
    participant Frontend as BluCare+ Frontend
    participant API as FastAPI /hospitals/nearby
    participant FacService as FacilitiesService
    participant Overpass as OSM Overpass API
    participant Distance as Haversine Engine
    participant MapsURLs as Google Maps URL Builder

    User->>Frontend: Click "Find Nearby Facilities"
    Frontend->>User: Request Geolocation Permission
    User-->>Frontend: Coordinates (lat=18.5204, lng=73.8567)
    Frontend->>API: GET /api/v1/hospitals/nearby?lat=18.5204&lng=73.8567
    API->>FacService: search_nearby_async(lat, lng, radius=5000)
    
    par Query OpenStreetMap Overpass
        FacService->>Overpass: POST Overpass QL (amenity=hospital|clinic|doctors)
        Overpass-->>FacService: Raw Elements (Nodes, Ways, Relations)
    and Build Fallback & Discovery URLs
        FacService->>MapsURLs: build_google_maps_search_url(lat, lng, "hospitals")
        MapsURLs-->>FacService: Google Maps Universal Search Link
    end

    FacService->>Distance: Compute Great-Circle Distance for each POI
    Distance-->>FacService: Straight-line meters
    FacService->>FacService: Deduplicate, sort by proximity, truncate to limit
    FacService-->>API: NearbyFacilitiesResponse (facilities + external_search + attribution)
    API-->>Frontend: HTTP 200 JSON Response
    Frontend-->>User: Display Facility Cards & Direct Navigation Links
```

### 3.1 Graceful Degradation Matrix
| Condition | Overpass Response | API Status | Facilities List | Google Maps Link |
|---|---|---|---|---|
| Normal Operation | HTTP 200 with elements | `success` | Real OSM facilities | Populated |
| Sparse Area | HTTP 200 with 0 elements | `empty` | `[]` | Populated |
| Rate Limited (HTTP 429) | HTTP 429 | `unavailable` | `[]` | Populated |
| Overpass Timeout (>25s) | `httpx.TimeoutException` | `unavailable` | `[]` | Populated |
| No Internet / Down Server | Connection error | `unavailable` | `[]` | Populated |

**Guaranteed Invariant:** The user is never stranded with an unhandled exception or fake placeholder hospitals. Universal Google Maps search links are guaranteed whenever valid coordinates are supplied.

---

## 4. Database Schema & Relationships

```mermaid
erDiagram
    triage_sessions ||--o{ triage_messages : "contains (1:N)"
    triage_sessions ||--o{ triage_safety_events : "triggers (1:N)"
    triage_sessions ||--o{ triage_assessments : "generates (1:N)"

    triage_sessions {
        string id PK "UUID"
        string clerk_user_id "Indexed"
        string status "intake | assessment_ready | emergency | completed"
        json case_state "Structured PatientCase"
        text pending_question "Current follow-up"
        integer version "Optimistic locking"
        timestamp created_at
        timestamp updated_at
        timestamp closed_at
    }

    triage_messages {
        string id PK "UUID"
        string session_id FK "Cascade delete"
        string role "user | assistant | system"
        text content "Conversation turn text"
        integer turn_id
        string idempotency_key "Indexed"
        timestamp created_at
    }

    triage_safety_events {
        string id PK "UUID"
        string session_id FK "Cascade delete"
        string message_id
        string rule_id "e.g. CHEST_PAIN_RED_FLAG"
        string ruleset_version "1.0.0-provisional"
        string outcome "emergency_detected"
        timestamp created_at
    }

    triage_assessments {
        string id PK "UUID"
        string session_id FK "Cascade delete"
        string user_id "Indexed"
        string assessment_version "1.0.0"
        json assessment_json "Full validated clinical output"
        json evidence_source_ids "Array of EVID-XXX references"
        string safety_ruleset_version
        string rag_configuration_version
        timestamp created_at
    }
```

---

## 5. Security & Privacy Controls

1. **Patient Data Leak Prevention:**
   - Geolocation coordinates are only accepted on explicit facility discovery requests.
   - Medical symptoms, disease hypotheses, diagnoses, patient names, and session IDs are **strictly excluded** from all external Map and Overpass queries.
2. **Authentication Isolation:**
   - Every database query in `TriageRepository` filters by `clerk_user_id == authenticated_user_id`.
   - Access to `/api/v1/assessments/{id}` and `/api/v1/sessions/{id}/assessment` enforces ownership checks; unauthorized cross-user queries return 404.
3. **SQL & Injection Resistance:**
   - SQLAlchemy parameterized queries prevent SQL injection.
   - Overpass queries use strictly validated coordinate floats and fixed category enum values; patient text is never concatenated into Overpass QL.
4. **Security Headers:**
   - Middleware enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
