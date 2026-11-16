import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.repository import TriageRepository

settings.allow_dev_auth = True
settings.app_env = "testing"
client = TestClient(app, headers={"Authorization": "Bearer test_dev_token"})


def test_fever_multiturn_to_differential_assessment():
    """
    Scenario 1: Multi-turn intake from fever to complete differential assessment.
    Verifies:
    - 3-turn intake transitions to complete assessment
    - Up to 3 possible conditions with all required fields
    - Non-empty evidence citations
    - Exactly two actions: GET_AYURVEDIC_GUIDANCE and FIND_NEARBY_CLINICS
    """
    # Turn 1: User reports fever
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    assert start_resp.status_code == 200
    session_data = start_resp.json()
    thread_id = session_data["thread_id"]
    assert "fever" in session_data["message"].lower() or "how long" in session_data["message"].lower()

    # Turn 2: User reports duration
    t2_resp = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    assert t2_resp.status_code == 200
    t2_data = t2_resp.json()
    assert not t2_data["is_complete"]
    assert t2_data["stage"] == "intake"
    assert t2_data["assessment"] is None

    # Turn 3: User provides severity & associated symptom -> triggers assessment
    t3_resp = client.post(
        "/api/v1/session/message",
        json={"thread_id": thread_id, "message": "moderate, feeling weak"},
    )
    assert t3_resp.status_code == 200
    t3_data = t3_resp.json()

    assert t3_data["is_complete"] is True
    assert t3_data["stage"] == "post_prediction"
    assert t3_data["risk_level"] in ["low", "moderate"]
    assert t3_data["assessment_id"] is not None

    assessment = t3_data["assessment"]
    assert assessment is not None
    assert "possible_conditions" in assessment
    assert 1 <= len(assessment["possible_conditions"]) <= 3

    # Check structure of each condition
    for cond in assessment["possible_conditions"]:
        assert "condition_id" in cond and cond["condition_id"].startswith("cond-")
        assert "name" in cond and len(cond["name"]) > 0
        assert "explanation" in cond and len(cond["explanation"]) > 0
        assert "supporting_evidence_ids" in cond and len(cond["supporting_evidence_ids"]) > 0
        assert "findings_against" in cond
        assert "uncertainties" in cond
        assert "recommended_care_setting" in cond

    # Check sources citations
    assert len(assessment["sources"]) > 0
    for src in assessment["sources"]:
        assert "id" in src
        assert "title" in src

    # Verify exactly two actions
    actions = t3_data["actions"]
    assert len(actions) == 2
    action_ids = [a["id"] for a in actions]
    assert "GET_AYURVEDIC_GUIDANCE" in action_ids
    assert "FIND_NEARBY_CLINICS" in action_ids

    top_condition_id = assessment["possible_conditions"][0]["condition_id"]
    for act in actions:
        assert act["condition_id"] == top_condition_id


def test_action_branch_ayurvedic_guidance():
    """
    Scenario 2: Execute GET_AYURVEDIC_GUIDANCE action.
    Verifies:
    - Dietary & lifestyle recommendations returned
    - Contraindication warnings (pregnancy, allergies, liver/kidney) present
    - Explicit disclaimer that it complements (not replaces) conventional care
    - Genuine citations from AYUSH corpus
    """
    # 1. Complete intake to generate assessment
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    t3_resp = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})
    top_cond_id = t3_resp.json()["assessment"]["possible_conditions"][0]["condition_id"]

    # 2. Execute GET_AYURVEDIC_GUIDANCE
    action_resp = client.post(
        "/api/v1/session/action",
        json={
            "thread_id": thread_id,
            "action_id": "GET_AYURVEDIC_GUIDANCE",
            "condition_id": top_cond_id,
        },
    )
    assert action_resp.status_code == 200
    action_data = action_resp.json()
    msg = action_data["message"]

    # Check key requirements in message
    assert "Ayurvedic" in msg
    assert "Contraindications" in msg or "contraindicated" in msg.lower()
    assert "complements" in msg.lower() or "not replace" in msg.lower() or "licensed" in msg.lower()

    # Check sources returned
    sources = action_data["sources"]
    assert len(sources) > 0
    ayu_source_ids = [s["id"] for s in sources]
    assert any("AYU" in sid or "MED" in sid for sid in ayu_source_ids)


def test_action_branch_find_nearby_clinics():
    """
    Scenario 3: Execute FIND_NEARBY_CLINICS action.
    Verifies:
    - Healthcare facilities returned
    - Google Maps search URL included
    - Zero clinical details or PII in external search URL
    """
    # 1. Complete intake to generate assessment
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    t3_resp = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})
    top_cond_id = t3_resp.json()["assessment"]["possible_conditions"][0]["condition_id"]

    # 2. Execute FIND_NEARBY_CLINICS
    action_resp = client.post(
        "/api/v1/session/action",
        json={
            "thread_id": thread_id,
            "action_id": "FIND_NEARBY_CLINICS",
            "condition_id": top_cond_id,
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assert action_resp.status_code == 200
    action_data = action_resp.json()
    msg = action_data["message"]

    assert "Verified Healthcare Clinics" in msg or "Clinics" in msg
    assert "google.com/maps/search" in msg

    # Verify privacy: no symptoms in maps URL
    assert "fever" not in msg.split("google.com/maps/search")[1].split(")")[0].lower()
    assert "weakness" not in msg.split("google.com/maps/search")[1].split(")")[0].lower()


def test_invalid_condition_id_rejection():
    """
    Scenario 4: Send action execution request with an invalid condition_id.
    Verifies:
    - Returns 400 Bad Request
    - Clear error message indicating invalid condition_id
    """
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})

    invalid_resp = client.post(
        "/api/v1/session/action",
        json={
            "thread_id": thread_id,
            "action_id": "GET_AYURVEDIC_GUIDANCE",
            "condition_id": "cond_invalid_nonexistent_999",
        },
    )
    assert invalid_resp.status_code == 400
    err = invalid_resp.json()["detail"]
    assert "Invalid condition_id" in err


def test_emergency_scenario_bypasses_assessment_and_actions():
    """
    Scenario 5: Red flag emergency message.
    Verifies:
    - Immediate emergency triage response
    - Assessment is NOT generated
    - Actions list is empty
    - Emergency helplines (108, 112) provided
    """
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "hello"})
    thread_id = start_resp.json()["thread_id"]

    chat_resp = client.post(
        "/api/v1/session/message",
        json={
            "thread_id": thread_id,
            "message": "I have crushing chest pain radiating to my left arm with shortness of breath",
        },
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()

    assert data["risk_level"] == "emergency"
    assert data["assessment"] is None
    assert len(data["actions"]) == 0
    assert "108" in data["message"] or "112" in data["message"]


def test_session_persistence_after_assessment():
    """
    Scenario 6: Verify assessment persistence in database and history reload.
    """
    # 1. Complete intake
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    t3_resp = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})
    assessment_id = t3_resp.json()["assessment_id"]
    assert assessment_id is not None

    # 2. Check repository persistence
    db = SessionLocal()
    try:
        persisted = TriageRepository.get_latest_assessment(db, thread_id)
        assert persisted is not None
        assert persisted.id == assessment_id
        assert "possible_conditions" in persisted.assessment_json
    finally:
        db.close()

    # 3. Check history endpoint
    hist_resp = client.get(f"/api/v1/session/{thread_id}/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["status"] == "completed"
    assert len(hist_data["messages"]) >= 4
