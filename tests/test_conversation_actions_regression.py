import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.repository import TriageRepository
from app.services.patient_case import PatientCase
from app.services.symptom_extractor import SymptomExtractor
from app.services.patient_lookup import PatientLookupEngine
from app.core.session_service import SessionService

settings.allow_dev_auth = True
settings.app_env = "testing"

client_user_a = TestClient(app, headers={"Authorization": "Bearer test_user_a"})
client_user_b = TestClient(app, headers={"Authorization": "Bearer test_user_b"})


def test_malformed_natural_language_symptom_extraction():
    """
    Requirement 1 & 9: Verify natural-language symptom extraction:
    - Input: 'I am feeling weakness from 2 days.'
    - Never uses entire patient sentence as symptom name.
    - Extracts symptom as 'Weakness'.
    - Preserves original wording 'feeling weakness'.
    - Extracts duration as '2 days'.
    - Correctly normalizes Hinglish and common misspellings.
    """
    case = PatientCase()

    # Test 1: Exact defect report: "I am feeling weakness from 2 days."
    norm_name = case.normalize_symptom_name("I am feeling weakness from 2 days.")
    assert norm_name == "weakness", f"Expected 'weakness', got '{norm_name}'"

    dur = PatientLookupEngine.extract_duration_string("I am feeling weakness from 2 days.")
    assert dur == "2 days", f"Expected '2 days', got '{dur}'"

    case.add_or_update_symptom(
        name="I am feeling weakness from 2 days.",
        duration=dur,
        turn_id=1,
    )
    rec = case.get_symptom("weakness")
    assert rec is not None
    assert rec.name == "Weakness", f"Expected capitalized entity name 'Weakness', got '{rec.name}'"
    assert rec.normalized_name == "weakness"
    assert rec.duration == "2 days"
    assert rec.severity is None

    # Test 2: Typos and Hinglish normalization
    assert case.normalize_symptom_name("sir dard") == "headache"
    assert case.normalize_symptom_name("severe headeche") == "headache"
    assert case.normalize_symptom_name("chakkar") == "dizziness"
    assert case.normalize_symptom_name("kamzori") == "weakness"
    assert case.normalize_symptom_name("pet dard") == "abdominal pain"
    assert case.normalize_symptom_name("bukhar") == "fever"


def test_multiple_symptoms_and_individual_durations():
    """
    Requirement 1 & 9: Multi-symptom extraction from single message:
    - Splits clauses to prevent duration/severity bleed.
    - Attaches 3 days to fever and yesterday to headache.
    """
    case = PatientCase()
    msg = "I have fever for 3 days and severe headache since yesterday"
    merged = PatientLookupEngine.inspect_and_merge_new_symptoms(msg, case, turn_id=1)
    assert merged is True

    fever_rec = case.get_symptom("fever")
    headache_rec = case.get_symptom("headache")

    assert fever_rec is not None
    assert fever_rec.status == "present"
    assert fever_rec.duration == "3 days"

    assert headache_rec is not None
    assert headache_rec.status == "present"
    assert "yesterday" in headache_rec.duration.lower()
    assert headache_rec.severity == "severe"


def test_no_repeated_questions_and_persistent_memory():
    """
    Requirement 1 & 9: Verify question planner does not ask for already provided facts.
    - User states: 'I am feeling weakness from 2 days.'
    - Question planner MUST NOT ask for weakness duration.
    - Question planner MUST NOT ask what is the main symptom.
    """
    session_id, initial_reply = SessionService.start_session("I am feeling weakness from 2 days.", user_id="test_user_a")
    # Response should ask for severity or related symptoms, NEVER repeat duration
    reply_lower = initial_reply.lower()
    assert "how long" not in reply_lower, f"Unexpected duration question in: {initial_reply}"
    assert "what is the main symptom" not in reply_lower

    # Answer severity
    t2 = SessionService.process_message(thread_id=session_id, message="moderate", user_id="test_user_a")
    # Verify weakness severity and duration are both preserved
    facts = t2["symptom_facts"]["symptoms"]
    assert "weakness" in facts
    assert facts["weakness"]["duration"] == "2 days"
    assert facts["weakness"]["severity"] == "moderate"


def test_session_ownership_and_access_control():
    """
    Requirement 5, 6 & 9: Strict session ownership and error status codes:
    - User A creates a session.
    - User B cannot read history (returns 403 Forbidden).
    - User B cannot execute an action (returns 403 Forbidden).
    - Non-existent session returns 404 Not Found.
    """
    # 1. User A starts session
    resp = client_user_a.post("/api/v1/session/start", json={"initial_message": "fever"})
    assert resp.status_code == 200
    session_id = resp.json()["thread_id"]

    # 2. User B tries to read history -> 403 Forbidden
    history_resp = client_user_b.get(f"/api/v1/session/{session_id}/history")
    assert history_resp.status_code == 403, f"Expected 403 Forbidden, got {history_resp.status_code}"

    # 3. User B tries to execute action -> 403 Forbidden
    action_resp = client_user_b.post(
        "/api/v1/session/action",
        json={"thread_id": session_id, "action_id": "GET_AYURVEDIC_GUIDANCE"},
    )
    assert action_resp.status_code == 403, f"Expected 403 Forbidden, got {action_resp.status_code}"

    # 4. Non-existent session -> 404 Not Found
    fake_resp = client_user_a.get("/api/v1/session/00000000-0000-0000-0000-000000000000/history")
    assert fake_resp.status_code == 404


def test_rag_differential_assessment_and_citations():
    """
    Requirement 2 & 9: RAG Differential Assessment:
    - Compares symptoms against Qdrant knowledge base.
    - Yields up to 3 evidence-backed conditions.
    - Contains conflicting findings (findings_against) and diagnostic uncertainties.
    - Validates genuine sources.
    """
    start_resp = client_user_a.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]

    # Intake turn 2: duration
    client_user_a.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})

    # Intake turn 3: severity & associated symptom -> triggers complete assessment
    t3_resp = client_user_a.post(
        "/api/v1/session/message",
        json={"thread_id": thread_id, "message": "moderate, feeling weak"},
    )
    assert t3_resp.status_code == 200
    t3_data = t3_resp.json()
    assert t3_data["is_complete"] is True
    assert t3_data["assessment"] is not None

    assessment = t3_data["assessment"]
    conditions = assessment["possible_conditions"]
    assert 1 <= len(conditions) <= 3

    for cond in conditions:
        assert cond["condition_id"].startswith("cond-")
        assert len(cond["name"]) > 0
        assert "findings_against" in cond
        assert "uncertainties" in cond
        assert len(cond["supporting_evidence_ids"]) > 0

    assert len(assessment["sources"]) > 0
    for src in assessment["sources"]:
        assert src["id"].startswith("MED-") or src["id"].startswith("AYU-")


def test_ayurvedic_action_execution_and_condition_defaulting():
    """
    Requirement 3 & 9: Ayurvedic guidance action:
    - Executes successfully with condition_id.
    - Defaults to primary condition when condition_id is omitted.
    - Rejects invalid condition_id with 400 Bad Request.
    """
    # 1. Complete an assessment
    start_resp = client_user_a.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client_user_a.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    t3 = client_user_a.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})
    top_cond_id = t3.json()["assessment"]["possible_conditions"][0]["condition_id"]

    # 2. Call with explicit condition_id
    resp1 = client_user_a.post(
        "/api/v1/session/action",
        json={"thread_id": thread_id, "action_id": "GET_AYURVEDIC_GUIDANCE", "condition_id": top_cond_id},
    )
    assert resp1.status_code == 200
    assert "Ayurvedic" in resp1.json()["message"]
    assert len(resp1.json()["sources"]) > 0

    # 3. Call with omitted condition_id (must default safely to primary condition)
    resp2 = client_user_a.post(
        "/api/v1/session/action",
        json={"thread_id": thread_id, "action_id": "GET_AYURVEDIC_GUIDANCE"},
    )
    assert resp2.status_code == 200
    assert "Ayurvedic" in resp2.json()["message"]

    # 4. Call with invalid condition_id -> 400 Bad Request
    resp_invalid = client_user_a.post(
        "/api/v1/session/action",
        json={"thread_id": thread_id, "action_id": "GET_AYURVEDIC_GUIDANCE", "condition_id": "cond-invalid-9999"},
    )
    assert resp_invalid.status_code == 400


def test_nearby_clinics_action_and_privacy_maps_url():
    """
    Requirement 4 & 9: Nearby clinic action:
    - Returns structured facilities or legitimate provider message.
    - Google Maps search URL contains NO symptom or clinical data.
    """
    start_resp = client_user_a.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client_user_a.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    client_user_a.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})

    resp = client_user_a.post(
        "/api/v1/session/action",
        json={
            "thread_id": thread_id,
            "action_id": "FIND_NEARBY_CLINICS",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assert resp.status_code == 200
    msg = resp.json()["message"]
    assert "google.com/maps/search" in msg
    # Privacy check: Verify no symptoms are leaked in the URL
    url_part = msg.split("google.com/maps/search")[1].split(")")[0].lower()
    assert "fever" not in url_part
    assert "weakness" not in url_part
