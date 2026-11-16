import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.session_service import SessionService
from app.services.patient_case import PatientCase, FactStatus
from app.services.question_planner import QuestionPlanner
from app.facilities.service import FacilitiesService
from app.facilities.maps_urls import build_google_maps_search_url

settings.allow_dev_auth = True
settings.app_env = "testing"
client = TestClient(app, headers={"Authorization": "Bearer test_fix_token"})


def test_fever_extended_clinical_intake_flow():
    """
    Verifies Section 5 of fix.md:
    1. Patient states: 'fever for 2 days' -> bot asks about thermometer measurement.
    2. Patient answers: '101.5 F with thermometer' -> bot records objective temperature.
    3. Patient answers associated symptoms -> bot transitions to evidence-backed differential.
    """
    user_id = "test_fever_extended"
    
    # Turn 1: Patient reports fever for 2 days
    session_id, reply_1 = SessionService.start_session("fever for 2 days", user_id=user_id)
    reply_1_lower = reply_1.lower()
    
    # Must NOT produce final assessment prematurely
    assert "thermometer" in reply_1_lower or "check your temperature" in reply_1_lower or "reading" in reply_1_lower
    
    # Turn 2: Patient reports objective temperature measurement
    t2 = SessionService.process_message(session_id, "101.5 F with thermometer", user_id=user_id)
    assert t2["is_complete"] is False
    assert t2["risk_level"] == "not_assessed"
    assert t2["symptom_facts"]["symptoms"]["fever"]["measured_value"].upper() == "101.5 F"
    
    # Next question must explore associated symptoms
    reply_2_lower = t2["message"].lower()
    assert "symptom" in reply_2_lower or "chills" in reply_2_lower or "cough" in reply_2_lower
    
    # Turn 3: Patient reports associated and denied symptoms
    t3 = SessionService.process_message(
        session_id,
        "no cough or vomiting, but have body aches and chills",
        user_id=user_id,
    )
    assert t3["is_complete"] is True
    assert t3["stage"] == "post_prediction"
    assert t3["assessment"] is not None
    assert len(t3["assessment"]["possible_conditions"]) >= 1
    
    # Check that denied and associated symptoms were parsed correctly
    facts = t3["symptom_facts"]
    assert "denied_symptoms" in facts
    assert any("cough" in s.lower() or "vomiting" in s.lower() for s in facts["denied_symptoms"])


def test_weakness_clinical_differentiation():
    """
    Verifies Section 12 of fix.md:
    Patient reporting weakness is asked to differentiate generalized fatigue
    from focal / unilateral neurological weakness.
    """
    case = PatientCase()
    case.add_or_update_symptom("weakness", duration="3 days", turn_id=1)
    
    gap = QuestionPlanner.evaluate_clinical_gap(case, turn_id=1)
    assert gap.is_complete is False
    assert gap.category == "symptom_character"
    q_lower = gap.next_question.lower()
    assert "entire body" in q_lower or "one side" in q_lower or "limbs" in q_lower


def test_google_maps_search_privacy():
    """
    Verifies that Google Maps search URLs NEVER include clinical symptoms,
    disease names, or sensitive patient data.
    """
    import urllib.parse
    url_hospital = build_google_maps_search_url(18.456229, 73.8710766, "hospitals")
    url_clinic = build_google_maps_search_url(18.456229, 73.8710766, "clinics")
    
    assert "https://www.google.com/maps/search/" in url_hospital
    assert "fever" not in url_hospital.lower()
    assert "weakness" not in url_hospital.lower()
    assert "malaria" not in url_hospital.lower()
    assert "dengue" not in url_hospital.lower()
    assert "18.456229,73.8710766" in urllib.parse.unquote(url_hospital)
    assert "18.456229,73.8710766" in urllib.parse.unquote(url_clinic)


def test_facilities_service_10km_fallback_behavior():
    """
    Verifies Section 10 of fix.md:
    When 5km query returns zero elements, the service automatically retries at 10km.
    If still 0, it does NOT say 'no hospitals exist' but provides verified Google Maps links.
    """
    service = FacilitiesService()
    
    with patch.object(service.scraper, "scrape_facilities", return_value=[]):
        res = service.search_nearby(18.456229, 73.8710766)
        assert res.status == "empty"
        assert len(res.facilities) == 0
        assert "healthcare facilities" in res.message.lower()
        assert "do not exist" not in res.message.lower()
        assert "google_maps" in res.external_search
        assert res.external_search["google_maps"].hospitals_url is not None
