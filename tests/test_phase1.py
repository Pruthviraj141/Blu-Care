import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.session import init_db, SessionLocal
from app.db.repository import TriageRepository
from app.services.patient_case import PatientCase, FactStatus
from app.services.safety_engine import SafetyEngine
from app.services.symptom_extractor import SymptomExtractor, ExtractedSymptoms
from app.services.question_planner import QuestionPlanner
from app.core.session_service import SessionService

# Ensure DB initialized for test session
init_db()


@pytest.fixture
def client():
    # Set testing environment & allow dev auth during tests
    old_env = settings.app_env
    old_dev_auth = settings.allow_dev_auth
    settings.app_env = "testing"
    settings.allow_dev_auth = True
    with TestClient(app) as test_client:
        yield test_client
    settings.app_env = old_env
    settings.allow_dev_auth = old_dev_auth


# =====================================================================
# A. AUTHENTICATION TESTS
# =====================================================================

def test_auth_rejection_when_dev_auth_disabled(client):
    """When allow_dev_auth is False and no token is provided, 401 is returned."""
    settings.allow_dev_auth = False
    response = client.post("/api/v1/session/start", json={"initial_message": "Hello"})
    assert response.status_code == 401
    assert "Missing Authorization Bearer token header" in response.json()["detail"]


def test_auth_rejection_on_invalid_token(client):
    """Providing a garbage token returns 401."""
    settings.allow_dev_auth = False
    response = client.post(
        "/api/v1/session/start",
        json={"initial_message": "Hello"},
        headers={"Authorization": "Bearer invalid.token.payload"},
    )
    assert response.status_code == 401


def test_dev_auth_allowed_when_enabled(client):
    """When allow_dev_auth is True in testing, requests proceed with dev identity."""
    settings.allow_dev_auth = True
    response = client.post("/api/v1/session/start", json={"initial_message": "Hello"})
    assert response.status_code == 200
    assert "thread_id" in response.json()


# =====================================================================
# B. SESSION & PERSISTENCE TESTS
# =====================================================================

def test_session_lifecycle_and_isolation(client):
    """Session created by User A cannot be accessed or deleted by User B."""
    db = SessionLocal()
    try:
        # Create session for User A
        sess_a = TriageRepository.create_session(db, clerk_user_id="user_alice_123")
        TriageRepository.add_message(db, sess_a.id, "user", "My ankle hurts")

        # User B attempts to access User A's session
        with pytest.raises(Exception):
            SessionService.get_session_history(sess_a.id, user_id="user_bob_456")

        # User A successfully retrieves session history
        history = SessionService.get_session_history(sess_a.id, user_id="user_alice_123")
        assert len(history["messages"]) == 1
        assert history["messages"][0].text == "My ankle hurts"

        # List sessions returns only User A's sessions
        alice_sessions = SessionService.list_user_sessions("user_alice_123")
        assert any(s.thread_id == sess_a.id for s in alice_sessions)
        bob_sessions = SessionService.list_user_sessions("user_bob_456")
        assert not any(s.thread_id == sess_a.id for s in bob_sessions)
    finally:
        db.close()


def test_session_deletion_cascades(client):
    """Deleting a session removes messages from database."""
    db = SessionLocal()
    try:
        sess = TriageRepository.create_session(db, clerk_user_id="user_test_delete")
        TriageRepository.add_message(db, sess.id, "user", "Hello to delete")

        assert len(TriageRepository.get_messages(db, sess.id)) == 1

        deleted = SessionService.delete_session(sess.id, user_id="user_test_delete")
        assert deleted is True

        # Messages must be gone
        assert len(TriageRepository.get_messages(db, sess.id)) == 0
        assert TriageRepository.get_session(db, sess.id, "user_test_delete") is None
    finally:
        db.close()


# =====================================================================
# C. STRUCTURED PATIENT-CASE & FACT MERGING TESTS
# =====================================================================

def test_patient_case_explicit_corrections():
    """Explicit corrections replace old values and record replaced_value provenance."""
    case = PatientCase()

    # Initial value
    case.update_single_fact("duration", "yesterday", FactStatus.PROVIDED, turn_id=1)
    assert case.duration.value == "yesterday"
    assert case.duration.replaced_value is None

    # Explicit correction
    case.update_single_fact("duration", "3 days ago", FactStatus.PROVIDED, turn_id=2)
    assert case.duration.value == "3 days ago"
    assert case.duration.replaced_value == "yesterday"


def test_patient_case_list_merging_preserves_order():
    """List merging preserves insertion order without arbitrary set() reordering."""
    case = PatientCase()
    case.merge_list_items("associated_symptoms", ["headache", "nausea"])
    case.merge_list_items("associated_symptoms", ["fatigue", "headache"])  # duplicate headache

    assert case.associated_symptoms == ["headache", "nausea", "fatigue"]


def test_patient_case_denied_symptoms():
    """Explicitly absent symptoms are recorded in denied_symptoms."""
    case = PatientCase()
    case.merge_list_items("denied_symptoms", ["fever", "vomiting"])
    assert "fever" in case.denied_symptoms
    assert "vomiting" in case.denied_symptoms


# =====================================================================
# D. DETERMINISTIC QUESTION PLANNING TESTS
# =====================================================================

def test_question_planner_prioritizes_missing_facts():
    """Planner asks for duration and severity when primary symptom is provided."""
    case = PatientCase()
    case.update_single_fact("primary_symptom", "Headache", FactStatus.PROVIDED, turn_id=1)

    is_complete, missing, question = QuestionPlanner.evaluate_intake(case)
    assert is_complete is False
    assert missing == "duration"
    assert "long" in question.lower()

    # Provide duration
    case.update_single_fact("duration", "2 days", FactStatus.PROVIDED, turn_id=2)
    is_complete, missing, question = QuestionPlanner.evaluate_intake(case)
    assert is_complete is False
    assert missing == "severity"
    assert "scale" in question.lower()

    # Provide severity and associated symptoms
    case.update_single_fact("severity", "6/10", FactStatus.PROVIDED, turn_id=3)
    case.merge_list_items("denied_symptoms", ["no fever"])
    is_complete, missing, question = QuestionPlanner.evaluate_intake(case)
    assert is_complete is True
    assert missing is None


# =====================================================================
# E. EMERGENCY SAFETY ENGINE TESTS
# =====================================================================

def test_emergency_detection_on_chest_pain():
    """Red flag symptoms trigger immediate emergency evaluation."""
    result = SafetyEngine.evaluate("I have severe crushing chest pain radiating to my jaw")
    assert result.is_emergency is True
    assert result.rule_id == "EMERGENCY-CHEST-PAIN"
    assert result.outcome == "emergency_detected"
    assert "EMERGENCY WARNING" in result.emergency_message


def test_emergency_cannot_be_downgraded_in_session(client):
    """When an emergency symptom is reported, normal intake stops and emergency is persisted."""
    settings.allow_dev_auth = True
    thread_id, reply = SessionService.start_session("I cannot breathe and my lips are turning blue", "user_emergency_test")
    assert "EMERGENCY WARNING" in reply

    # Verify session is marked emergency in DB
    db = SessionLocal()
    try:
        sess = TriageRepository.get_session(db, thread_id, "user_emergency_test")
        assert sess.status == "emergency"
        assert len(sess.safety_events) >= 1
        assert sess.safety_events[0].rule_id == "EMERGENCY-SEVERE-RESPIRATORY"
    finally:
        db.close()


# =====================================================================
# F. MULTI-TURN INTEGRATION TEST
# =====================================================================

def test_multi_turn_intake_and_rag_bridge():
    """Simulates multi-turn intake: intake questions -> correction -> complete RAG bridge."""
    user_id = "user_integration_test_turn"

    # Turn 1: Start with primary symptom
    thread_id, reply_1 = SessionService.start_session("I have had a headache since yesterday", user_id=user_id)
    assert thread_id is not None
    assert "scale" in reply_1.lower() or "severe" in reply_1.lower() or "long" in reply_1.lower()

    # Turn 2: Provide severity & denied symptom
    turn_2 = SessionService.process_message(thread_id, "My headache is 6/10, no fever or vomiting", user_id=user_id)
    assert turn_2["stage"] in ("intake", "post_prediction")
    facts = turn_2["symptom_facts"]
    assert facts["severity"] == "6/10"
    assert "fever" in facts["denied_symptoms"] or "no fever" in facts["denied_symptoms"]

    # Turn 3: Explicit correction
    turn_3 = SessionService.process_message(thread_id, "Actually, it started 3 days ago", user_id=user_id)
    assert "3 days" in turn_3["symptom_facts"]["duration"]
