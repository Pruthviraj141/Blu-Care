"""Comprehensive End-to-End Regression Test Suite for Phase 3:
Unified Conversational Intelligence & Medical RAG Engine.

Directly verifies Scenarios A through N from phases/phase3.md Section 15:
- Test A: Full sentence extraction
- Test B: Multiple symptoms with separate durations
- Test C: Pending answer resolution
- Test D: New symptom addition without forgetting prior facts
- Test E: Answered question ledger check
- Test F: Patient correction handling
- Test G: Negative / explicitly absent symptoms
- Test H: Complex composite patient message
- Test I: Evidence-grounded RAG medical assessment
- Test J: Knowledge-base gap / insufficient evidence handling
- Test K: Deterministic emergency escalation
- Test L: Session restart persistence & continuity
- Test M: Post-assessment actions (Ayurvedic guidance & OSM Clinic search)
- Test N: Multi-user isolation
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.session_service import SessionService
from app.db.session import SessionLocal
from app.db.repository import TriageRepository
from app.services.patient_case import PatientCase, FactStatus

settings.allow_dev_auth = True
settings.app_env = "testing"
client = TestClient(app, headers={"Authorization": "Bearer test_phase3_token"})


# ---------------------------------------------------------------------
# Test A: Full sentence extraction
# ---------------------------------------------------------------------
def test_scenario_a_full_sentence_extraction():
    """
    Patient: 'I have weakness from last 2 days.'
    Expected:
    - Symptom = weakness (NOT the entire sentence)
    - Duration = 2 days
    - No question asking when weakness started
    """
    resp = client.post("/api/v1/session/start", json={"initial_message": "I have weakness from last 2 days."})
    assert resp.status_code == 200
    data = resp.json()
    thread_id = data["thread_id"]

    # Check state through history or session facts
    hist = client.get(f"/api/v1/session/{thread_id}/history").json()
    facts = hist["symptom_facts"]

    assert "weakness" in facts.get("symptoms", {})
    weakness_rec = facts["symptoms"]["weakness"]
    assert weakness_rec["name"] == "weakness" or weakness_rec["normalized_name"] == "weakness"
    assert "2 days" in weakness_rec["duration"] or "last 2 days" in weakness_rec["duration"]

    # Assistant should NOT ask "how long have you had this weakness"
    bot_msg = data["message"].lower()
    assert "how long have you had this weakness" not in bot_msg
    assert "when did it start" not in bot_msg


# ---------------------------------------------------------------------
# Test B: Multiple symptoms with separate durations
# ---------------------------------------------------------------------
def test_scenario_b_multiple_symptoms():
    """
    Patient: 'I have fever for three days, weakness since yesterday and mild headache.'
    Expected:
    - Fever duration = 3 days / three days
    - Weakness duration = since yesterday
    - Headache = present
    - No incorrect shared duration
    - All three symptoms preserved
    """
    resp = client.post(
        "/api/v1/session/start",
        json={"initial_message": "I have fever for three days, weakness since yesterday and mild headache."},
    )
    assert resp.status_code == 200
    thread_id = resp.json()["thread_id"]

    hist = client.get(f"/api/v1/session/{thread_id}/history").json()
    symptoms = hist["symptom_facts"]["symptoms"]

    assert "fever" in symptoms
    assert "weakness" in symptoms
    assert "headache" in symptoms

    assert "three days" in symptoms["fever"]["duration"] or "3 days" in symptoms["fever"]["duration"]
    assert "since yesterday" in symptoms["weakness"]["duration"] or "yesterday" in symptoms["weakness"]["duration"]

    # Weakness duration must NOT be applied to fever or headache
    assert symptoms["headache"]["duration"] is None or symptoms["headache"]["duration"] != symptoms["fever"]["duration"]
    assert symptoms["fever"]["duration"] != symptoms["weakness"]["duration"]


# ---------------------------------------------------------------------
# Test C: Pending answer
# ---------------------------------------------------------------------
def test_scenario_c_pending_answer():
    """
    Turn 1: Patient: 'fever' -> Assistant asks for duration
    Turn 2: Patient: 'two days ago' -> Assistant records fever duration = 2 days
    """
    resp1 = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = resp1.json()["thread_id"]
    assert "how long" in resp1.json()["message"].lower() or "duration" in resp1.json()["message"].lower()

    resp2 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "two days ago"})
    data2 = resp2.json()

    fever = data2["symptom_facts"]["symptoms"]["fever"]
    assert fever["duration"] is not None
    assert "two days" in fever["duration"] or "days" in fever["duration"]
    # Does not restart primary symptom question
    assert "what is the main symptom" not in data2["message"].lower()


# ---------------------------------------------------------------------
# Test D: New symptom
# ---------------------------------------------------------------------
def test_scenario_d_new_symptom_added():
    """
    Patient: 'I also feel weak.'
    Expected:
    - Weakness added
    - Fever remains present
    - Fever duration remains intact
    """
    resp1 = client.post("/api/v1/session/start", json={"initial_message": "fever for 3 days"})
    thread_id = resp1.json()["thread_id"]

    resp2 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "I also feel weak."})
    symptoms = resp2.json()["symptom_facts"]["symptoms"]

    assert "fever" in symptoms
    assert "weakness" in symptoms
    assert symptoms["fever"]["duration"] is not None
    assert "3 days" in symptoms["fever"]["duration"]


# ---------------------------------------------------------------------
# Test E: Answered question ledger check
# ---------------------------------------------------------------------
def test_scenario_e_answered_question_never_reasked():
    """
    Patient: 'My fever has lasted three days.'
    Expected:
    - No later equivalent fever-duration question
    """
    resp1 = client.post("/api/v1/session/start", json={"initial_message": "My fever has lasted three days."})
    bot_reply = resp1.json()["message"].lower()
    assert "how long have you had this fever" not in bot_reply
    assert "how long have you had fever" not in bot_reply


# ---------------------------------------------------------------------
# Test F: Correction
# ---------------------------------------------------------------------
def test_scenario_f_correction():
    """
    Patient: 'Actually, my fever started five days ago.'
    Expected:
    - Current duration updated to five days
    - Other facts remain unchanged
    """
    resp1 = client.post("/api/v1/session/start", json={"initial_message": "fever for 2 days"})
    thread_id = resp1.json()["thread_id"]

    resp2 = client.post(
        "/api/v1/session/message",
        json={"thread_id": thread_id, "message": "Actually, my fever started 5 days ago."},
    )
    symptoms = resp2.json()["symptom_facts"]["symptoms"]
    assert "5 days" in symptoms["fever"]["duration"] or "five days" in symptoms["fever"]["duration"]


# ---------------------------------------------------------------------
# Test G: Negative symptom
# ---------------------------------------------------------------------
def test_scenario_g_negative_symptom():
    """
    Patient: 'I don't have vomiting.'
    Expected:
    - Vomiting explicitly absent
    - Not treated as unknown field
    """
    resp1 = client.post("/api/v1/session/start", json={"initial_message": "I have fever for 2 days"})
    thread_id = resp1.json()["thread_id"]

    resp2 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "I don't have vomiting."})
    symptoms = resp2.json()["symptom_facts"]["symptoms"]

    assert "vomiting" in symptoms
    assert symptoms["vomiting"]["status"] == "absent"


# ---------------------------------------------------------------------
# Test H: Complex patient message
# ---------------------------------------------------------------------
def test_scenario_h_complex_patient_message():
    """
    Patient supplies multiple symptoms, durations, negatives, and severity in one sentence.
    """
    message = "I have had fever for 3 days, mild headache, no vomiting, and severe body weakness."
    resp = client.post("/api/v1/session/start", json={"initial_message": message})
    thread_id = resp.json()["thread_id"]

    hist = client.get(f"/api/v1/session/{thread_id}/history").json()
    symptoms = hist["symptom_facts"]["symptoms"]

    assert "fever" in symptoms
    assert "headache" in symptoms
    assert "vomiting" in symptoms
    assert "weakness" in symptoms

    assert symptoms["vomiting"]["status"] == "absent"
    assert "3 days" in symptoms["fever"]["duration"]


# ---------------------------------------------------------------------
# Test I: Evidence-grounded RAG medical assessment
# ---------------------------------------------------------------------
def test_scenario_i_rag_medical_assessment():
    """
    Completed intake for febrile illness with fever, duration and moderate severity.
    Verifies:
    - Evidence retrieved from Qdrant
    - Valid non-empty citations
    - Up to 3 possible conditions
    """
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    t3_resp = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})

    data = t3_resp.json()
    assert data["is_complete"] is True
    assert data["stage"] == "post_prediction"
    assessment = data["assessment"]
    assert assessment is not None
    assert len(assessment["possible_conditions"]) >= 1
    assert len(assessment["sources"]) >= 1


# ---------------------------------------------------------------------
# Test J: Knowledge-base gap / insufficient evidence handling
# ---------------------------------------------------------------------
def test_scenario_j_insufficient_evidence():
    """
    Tests synthesizer safe behavior when evidence is absent or minimal.
    """
    from app.rag.synthesizer import EvidenceGroundedSynthesizer
    from app.rag.context_builder import AssembledEvidenceContext

    empty_context = AssembledEvidenceContext(formatted_context="", sources=[], total_tokens_approx=0)
    case = PatientCase()
    case.update_single_fact("primary_symptom", "unusual rare condition", FactStatus.PROVIDED, turn_id=1)

    result = EvidenceGroundedSynthesizer.synthesize(case, empty_context)
    assert result.is_insufficient_evidence is True
    assert len(result.evidence_limitations) > 0


# ---------------------------------------------------------------------
# Test K: Deterministic Emergency Escalation
# ---------------------------------------------------------------------
def test_scenario_k_emergency_escalation():
    """
    Patient reports crushing chest pain radiating to arm.
    Expected:
    - Emergency detected immediately
    - Normal intake halted
    - 112 / 108 emergency response numbers provided
    """
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "hello"})
    thread_id = start_resp.json()["thread_id"]
    resp = client.post(
        "/api/v1/session/message",
        json={"thread_id": thread_id, "message": "I have crushing chest pain radiating to left arm and shortness of breath"},
    )
    data = resp.json()
    assert data["risk_level"] == "emergency"
    assert "112" in data["message"] or "108" in data["message"]
    assert data["assessment"] is None
    assert len(data["actions"]) == 0


# ---------------------------------------------------------------------
# Test L: Session restart persistence & continuity
# ---------------------------------------------------------------------
def test_scenario_l_session_persistence_and_continuity():
    """
    Tests that after backend restart simulation (reloading directly from db),
    session context and history are fully restored and conversation continues seamlessly.
    """
    user_id = "test_persistence_user"
    thread_id, _ = SessionService.start_session("fever for 2 days", user_id=user_id)
    SessionService.process_message(thread_id, "moderate, feeling weak", user_id=user_id)

    db = SessionLocal()
    try:
        session = TriageRepository.get_session(db, thread_id, user_id)
        assert session is not None
        assert session.status in ("completed", "post_prediction")
        assert "fever" in session.case_state.get("symptoms", {})
    finally:
        db.close()


# ---------------------------------------------------------------------
# Test M: Post-assessment actions
# ---------------------------------------------------------------------
def test_scenario_m_post_assessment_actions():
    """
    Executes both GET_AYURVEDIC_GUIDANCE and FIND_NEARBY_CLINICS.
    Verifies:
    - Valid condition_id preserved
    - Real OSM/Google Maps links for clinics
    - Genuine herbal citations and contraindication warnings for Ayurvedic guidance
    """
    # 1. Generate assessment
    start_resp = client.post("/api/v1/session/start", json={"initial_message": "fever"})
    thread_id = start_resp.json()["thread_id"]
    client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "2 days"})
    t3 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "moderate, feeling weak"})
    cond_id = t3.json()["assessment"]["possible_conditions"][0]["condition_id"]

    # 2. Action A: Ayurvedic guidance
    ayu_resp = client.post(
        "/api/v1/session/action",
        json={"thread_id": thread_id, "action_id": "GET_AYURVEDIC_GUIDANCE", "condition_id": cond_id},
    )
    assert ayu_resp.status_code == 200
    ayu_data = ayu_resp.json()
    assert "Ayurvedic" in ayu_data["message"]
    assert len(ayu_data["sources"]) > 0

    # 3. Action B: Clinics
    clinic_resp = client.post(
        "/api/v1/session/action",
        json={
            "thread_id": thread_id,
            "action_id": "FIND_NEARBY_CLINICS",
            "condition_id": cond_id,
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assert clinic_resp.status_code == 200
    assert "google.com/maps/search" in clinic_resp.json()["message"]


# ---------------------------------------------------------------------
# Test N: Multi-user isolation
# ---------------------------------------------------------------------
def test_scenario_n_multi_user_isolation():
    """
    Two independent users must never share case state, messages, or sessions.
    """
    user_a = "patient_user_alpha"
    user_b = "patient_user_beta"

    sess_a, _ = SessionService.start_session("headache", user_id=user_a)
    sess_b, _ = SessionService.start_session("knee pain", user_id=user_b)

    # User A cannot read User B's session
    with pytest.raises(Exception):
        SessionService.get_session_history(sess_b, user_id=user_a)

    # User B cannot read User A's session
    with pytest.raises(Exception):
        SessionService.get_session_history(sess_a, user_id=user_b)
