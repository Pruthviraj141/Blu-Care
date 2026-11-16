import pytest
from app.core.session_service import SessionService
from app.db.session import SessionLocal
from app.db.repository import TriageRepository
from app.services.patient_case import PatientCase


def test_mandatory_multi_turn_regression_conversation():
    """
    Reproduces the exact multi-turn conversation mandated by the user:
    User: hi -> Assistant asks for main symptom
    User: fever -> Assistant asks for fever duration
    User: 3 days -> Records fever duration = 3 days
    User: weakness in body -> Assistant asks for weakness duration or missing relevant fact
    User: 3 days -> Records weakness duration = 3 days without overwriting fever duration

    Verifies:
    - Fever: present, duration 3 days
    - Weakness: present, duration 3 days
    - No duplicate symptoms
    - No repeated primary-symptom question
    - No repeated duration question
    - Both durations remain saved
    - Risk level is 'not_assessed' during incomplete intake
    - Next question selected using complete patient context
    """
    user_id = "test_user_regression"

    # Turn 1: User says "hi"
    session_id, initial_reply = SessionService.start_session(initial_message="hi", user_id=user_id)
    assert "main symptom" in initial_reply.lower() or "discomfort" in initial_reply.lower()

    # Turn 2: User says "fever"
    t2 = SessionService.process_message(thread_id=session_id, message="fever", user_id=user_id)
    assert not t2["is_complete"]
    assert t2["stage"] == "intake"
    assert t2["risk_level"] == "not_assessed"
    assert "fever" in t2["message"].lower()
    assert "how long" in t2["message"].lower() or "duration" in t2["message"].lower()

    # Turn 3: User says "3 days"
    t3 = SessionService.process_message(thread_id=session_id, message="3 days", user_id=user_id)
    assert not t3["is_complete"]
    assert t3["risk_level"] == "not_assessed"
    # Duration for fever is now recorded
    assert t3["symptom_facts"]["symptoms"]["fever"]["duration"] == "3 days"
    # Next question should NOT ask for fever duration or primary symptom again
    assert "how long have you had this fever" not in t3["message"].lower()
    assert "what is the main symptom" not in t3["message"].lower()

    # Turn 4: User says "weakness in body"
    t4 = SessionService.process_message(thread_id=session_id, message="weakness in body", user_id=user_id)
    assert not t4["is_complete"]
    assert t4["risk_level"] == "not_assessed"
    # Assistant asks only an appropriate question about weakness or genuinely missing fact
    assert "weakness" in t4["message"].lower()
    assert "how long" in t4["message"].lower()
    # Fever duration must STILL be 3 days
    assert t4["symptom_facts"]["symptoms"]["fever"]["duration"] == "3 days"

    # Turn 5: User says "3 days"
    t5 = SessionService.process_message(thread_id=session_id, message="3 days", user_id=user_id)
    facts = t5["symptom_facts"]

    # Verify Expected Patient State:
    symptoms = facts["symptoms"]
    assert "fever" in symptoms
    assert "weakness" in symptoms
    # No duplicate symptoms
    assert len([k for k in symptoms.keys() if "weakness" in k]) == 1
    assert len([k for k in symptoms.keys() if "fever" in k]) == 1

    # Fever: present, duration 3 days
    assert symptoms["fever"]["status"] == "present"
    assert symptoms["fever"]["duration"] == "3 days"

    # Weakness: present, duration 3 days
    assert symptoms["weakness"]["status"] == "present"
    assert symptoms["weakness"]["duration"] == "3 days"

    # Both durations remain saved simultaneously
    assert symptoms["fever"]["duration"] == "3 days"
    assert symptoms["weakness"]["duration"] == "3 days"

    # Next question must not repeat primary symptom or duration for fever or weakness
    next_msg = t5["message"].lower()
    assert "what is the main symptom" not in next_msg
    assert "how long have you had this fever" not in next_msg
    assert "how long have you had this weakness" not in next_msg


def test_session_restart_persistence():
    """
    Tests backend restarts and session state reload directly from database.
    Verifies that patient context is completely preserved across restarts.
    """
    user_id = "test_restart_user"
    session_id, _ = SessionService.start_session("hi", user_id=user_id)
    SessionService.process_message(session_id, "fever", user_id=user_id)
    SessionService.process_message(session_id, "3 days", user_id=user_id)
    SessionService.process_message(session_id, "weakness in body", user_id=user_id)
    SessionService.process_message(session_id, "3 days", user_id=user_id)

    # Simulate backend restart: create a new DB session and reload state directly
    db = SessionLocal()
    try:
        session_record = TriageRepository.get_session(db, session_id, clerk_user_id=user_id)
        assert session_record is not None
        restored_case = PatientCase(**session_record.case_state)

        # Assert full restored memory state
        assert "fever" in restored_case.symptoms
        assert "weakness" in restored_case.symptoms
        assert restored_case.symptoms["fever"].duration == "3 days"
        assert restored_case.symptoms["weakness"].duration == "3 days"
        assert restored_case.symptoms["fever"].status == "present"
        assert restored_case.symptoms["weakness"].status == "present"

        # Check ledger has recorded questions
        categories = [item.category for item in restored_case.question_ledger]
        assert "primary_symptom" in categories
        assert "symptom_duration" in categories
    finally:
        db.close()


def test_consecutive_messages_handling():
    """
    Tests patient providing multiple consecutive updates without losing prior facts.
    """
    user_id = "test_consecutive_user"
    session_id, _ = SessionService.start_session(None, user_id=user_id)

    # Message 1: User mentions fever with duration directly
    res1 = SessionService.process_message(session_id, "I have had a fever for 2 days", user_id=user_id)
    assert res1["symptom_facts"]["symptoms"]["fever"]["duration"] == "2 days"

    # Message 2: Consecutive message adding headache
    res2 = SessionService.process_message(session_id, "also severe headache", user_id=user_id)
    assert res2["symptom_facts"]["symptoms"]["fever"]["duration"] == "2 days"
    assert "headache" in res2["symptom_facts"]["symptoms"]
    assert res2["symptom_facts"]["symptoms"]["headache"]["status"] == "present"
    assert res2["symptom_facts"]["symptoms"]["headache"]["severity"] == "severe"

    # Message 3: Consecutive message adding negation
    res3 = SessionService.process_message(session_id, "no cough", user_id=user_id)
    assert res3["symptom_facts"]["symptoms"]["fever"]["duration"] == "2 days"
    assert res3["symptom_facts"]["symptoms"]["cough"]["status"] == "absent"


def test_exact_user_prompt_regression():
    """
    Tests the exact 6-turn sequence through the actual FastAPI HTTP endpoints:
    Turn 1: User: 'hi'
            AI: asks for symptoms
    Turn 2: User: 'fever'
            AI: asks for fever duration
    Turn 3: User: 'from last 2 days'
            AI: records fever duration = 2 days, asks next genuinely missing question
    Turn 4: User: 'feeling weak'
            AI: records weakness, preserves fever & duration, asks for weakness duration
    Turn 5: User: 'last 2 days'
            AI: records weakness duration = 2 days, does not restart intake
    Turn 6: User: 'fever'
            AI: recognizes fever already recorded, does not re-ask duration, asks next missing fact

    Expected final state:
    - Fever: present, duration 2 days
    - Weakness: present, duration 2 days
    - No duplicate symptoms
    - No repeated questions
    - Both durations preserved
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.config import settings

    settings.allow_dev_auth = True
    settings.app_env = "testing"
    client = TestClient(app, headers={"Authorization": "Bearer test_regression_token"})

    # Turn 1: hi
    resp1 = client.post("/api/v1/session/start", json={"query": "hi"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    thread_id = data1["thread_id"]
    assert "main symptom" in data1["message"].lower() or "discomfort" in data1["message"].lower()

    # Turn 2: fever
    resp2 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "fever"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["stage"] == "intake"
    assert data2["risk_level"] == "not_assessed"
    assert "how long" in data2["message"].lower() or "duration" in data2["message"].lower()
    assert "fever" in data2["message"].lower()

    # Turn 3: from last 2 days
    resp3 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "from last 2 days"})
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["risk_level"] == "not_assessed"
    assert data3["symptom_facts"]["symptoms"]["fever"]["duration"] == "2 days"
    assert "how long have you had this fever" not in data3["message"].lower()
    assert "what is the main symptom" not in data3["message"].lower()

    # Turn 4: feeling weak
    resp4 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "feeling weak"})
    assert resp4.status_code == 200
    data4 = resp4.json()
    assert data4["risk_level"] == "not_assessed"
    assert "weakness" in data4["message"].lower()
    assert "how long" in data4["message"].lower()
    # Fever and its duration must be preserved
    assert data4["symptom_facts"]["symptoms"]["fever"]["duration"] == "2 days"

    # Turn 5: last 2 days
    resp5 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "last 2 days"})
    assert resp5.status_code == 200
    data5 = resp5.json()
    assert data5["risk_level"] == "not_assessed"
    symptoms = data5["symptom_facts"]["symptoms"]
    assert symptoms["fever"]["duration"] == "2 days"
    assert symptoms["weakness"]["duration"] == "2 days"
    assert "what is the main symptom" not in data5["message"].lower()
    assert "how long have you had this fever" not in data5["message"].lower()
    assert "how long have you had this weakness" not in data5["message"].lower()

    # Turn 6: fever
    resp6 = client.post("/api/v1/session/message", json={"thread_id": thread_id, "message": "fever"})
    assert resp6.status_code == 200
    data6 = resp6.json()
    # Recognizes fever is already recorded
    assert "already recorded" in data6["message"].lower() or "fever" in data6["message"].lower()
    assert "how long have you had this fever" not in data6["message"].lower()
    assert "what is the main symptom" not in data6["message"].lower()

    # Verify final state
    final_symptoms = data6["symptom_facts"]["symptoms"]
    assert "fever" in final_symptoms
    assert "weakness" in final_symptoms
    assert len(final_symptoms) == 2
    assert final_symptoms["fever"]["status"] == "present"
    assert final_symptoms["fever"]["duration"] == "2 days"
    assert final_symptoms["weakness"]["status"] == "present"
    assert final_symptoms["weakness"]["duration"] == "2 days"

