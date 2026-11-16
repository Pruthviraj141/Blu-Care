import logging
import re
from typing import Optional, Tuple, List, Dict, Any
from pydantic import BaseModel, Field

from app.services.patient_case import PatientCase, FactStatus, SymptomRecord

logger = logging.getLogger(__name__)


class ClinicalGapResult(BaseModel):
    """Result of clinical information gap analysis."""
    is_complete: bool
    missing_area: Optional[str] = None
    next_question: Optional[str] = None
    clinical_justification: Optional[str] = None
    category: Optional[str] = None
    target_symptom: Optional[str] = None
    target_field: Optional[str] = None


class QuestionPlanner:
    """
    Intelligent Clinical Decision-Support Question Planner.
    Analyzes patient memory and evidence-supported candidate conditions
    to identify missing distinguishing findings and plan dynamic follow-up questions.
    """

    @classmethod
    def evaluate_intake(cls, case: PatientCase) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Legacy intake completeness evaluation for Phase 1 compatibility.
        """
        if not case.primary_symptom or case.primary_symptom.status != FactStatus.PROVIDED:
            return False, "primary_symptom", "What is the primary symptom you are experiencing?"
        if not case.duration or case.duration.status != FactStatus.PROVIDED:
            return False, "duration", "How long have you been experiencing this symptom?"
        if not case.severity or case.severity.status != FactStatus.PROVIDED:
            return False, "severity", "On a scale of 1 to 10, how severe would you rate your symptoms?"
        return True, None, None

    @classmethod
    def evaluate_clinical_gap(
        cls,
        case: PatientCase,
        turn_id: int = 1,
        candidate_conditions: Optional[List[Dict[str, Any]]] = None,
    ) -> ClinicalGapResult:
        """
        Evaluates clinical information completeness against medical evidence.
        Determines what facts are known vs unknown, identifies high-yield distinguishing questions,
        and provides an internal clinical justification for each question.
        """
        primary_sym = (
            case.primary_symptom.value.lower()
            if case.primary_symptom and case.primary_symptom.value
            else None
        )
        if not primary_sym and case.symptoms:
            # Pick first present symptom as primary
            present_syms = [k for k, v in case.symptoms.items() if v.status == "present"]
            if present_syms:
                primary_sym = present_syms[0]

        # -------------------------------------------------------------
        # Area 1: Primary Symptom (Chief Complaint)
        # -------------------------------------------------------------
        if not primary_sym or case.primary_symptom.status != FactStatus.PROVIDED:
            if not case.is_question_already_asked("primary_symptom", None, "primary_symptom"):
                q = "What is the main symptom or discomfort you are experiencing?"
                return ClinicalGapResult(
                    is_complete=False,
                    missing_area="chief_complaint",
                    next_question=q,
                    clinical_justification="Patient has not yet reported a chief presenting complaint.",
                    category="primary_symptom",
                    target_field="primary_symptom",
                )

        primary_rec = case.get_symptom(primary_sym)
        norm_sym = primary_rec.normalized_name if primary_rec else primary_sym

        # -------------------------------------------------------------
        # Area 2: Symptom Onset & Duration
        # -------------------------------------------------------------
        has_dur = bool((primary_rec and primary_rec.duration) or (case.duration and case.duration.value))
        if not has_dur:
            if not case.is_question_already_asked("symptom_duration", norm_sym, "duration"):
                # Natural focused phrasing
                q = f"How long have you had this {norm_sym}, or when did it first start?"
                return ClinicalGapResult(
                    is_complete=False,
                    missing_area="duration",
                    next_question=q,
                    clinical_justification=f"Onset and duration of {norm_sym} are unknown; critical for distinguishing acute, subacute, and chronic etiologies.",
                    category="symptom_duration",
                    target_symptom=norm_sym,
                    target_field="duration",
                )

        # Check known other symptoms
        known_other_symptoms = [
            k for k, v in case.symptoms.items() if k != norm_sym and (v.status in ("present", "absent"))
        ]
        has_sev_or_temp = bool(
            case.measured_temperature
            or (primary_rec and (primary_rec.severity or primary_rec.measured_value))
            or (case.severity and case.severity.value)
        )
        has_associated = bool(
            len(known_other_symptoms) > 0
            or case.denied_symptoms
            or case.associated_symptoms
            or case.is_question_already_asked("associated_symptoms", norm_sym, "associated_symptoms")
        )

        # If core clinical context across 4 key areas (chief complaint, duration, severity/measurement, and associated symptoms) is established:
        if has_dur and has_sev_or_temp and has_associated:
            logger.info(
                f"Intake clinical context satisfied for case (Primary: {primary_sym}, "
                f"Symptoms: {list(case.symptoms.keys())}, Turns: {case.turn_count})."
            )
            return ClinicalGapResult(
                is_complete=True,
                missing_area=None,
                next_question=None,
                clinical_justification="Sufficient clinical context gathered across core information areas for differential assessment.",
            )

        # Check if any other present symptom lacks duration
        for s_key, s_data in case.symptoms.items():
            if s_key != norm_sym and s_data.status == "present" and not s_data.duration:
                if not case.is_question_already_asked("symptom_duration", s_key, "duration"):
                    q = f"How long have you been experiencing this {s_data.name.lower()}?"
                    return ClinicalGapResult(
                        is_complete=False,
                        missing_area="duration",
                        next_question=q,
                        clinical_justification=f"Onset and duration of {s_data.name} are unknown; critical for temporal correlation.",
                        category="symptom_duration",
                        target_symptom=s_key,
                        target_field="duration",
                    )

        # -------------------------------------------------------------
        # Area 3: Objective Measurement vs Subjective Severity
        # -------------------------------------------------------------
        # For Fever: distinguish measured temperature from subjective warmth
        if norm_sym == "fever" or "fever" in case.symptoms:
            fever_rec = case.get_symptom("fever")
            has_measured_temp = bool(case.measured_temperature or (fever_rec and fever_rec.measured_value))
            temp_already_asked = case.is_question_already_asked("measured_temperature", "fever", "measured_temperature")

            if not has_measured_temp and not temp_already_asked:
                q = "Have you been able to check your temperature with a thermometer, and if so, what was the reading?"
                return ClinicalGapResult(
                    is_complete=False,
                    missing_area="objective_temperature",
                    next_question=q,
                    clinical_justification="Fever reported without objective temperature reading; distinguishing measured temperature from subjective warmth clarifies fever magnitude and triage severity.",
                    category="measured_temperature",
                    target_symptom="fever",
                    target_field="measured_temperature",
                )

        # For Weakness: distinguish generalized body fatigue from focal neurological weakness
        if norm_sym == "weakness":
            weakness_char_asked = case.is_question_already_asked("symptom_character", "weakness", "distribution")
            if not weakness_char_asked and len(case.symptoms) == 1:
                q = "Is this weakness affecting your entire body generally, or is it isolated to one side, face, or specific limbs?"
                return ClinicalGapResult(
                    is_complete=False,
                    missing_area="symptom_character",
                    next_question=q,
                    clinical_justification="Need to differentiate generalized systemic/metabolic fatigue from focal or unilateral neurological weakness requiring urgent triage.",
                    category="symptom_character",
                    target_symptom="weakness",
                    target_field="distribution",
                )

        # General severity if neither severity nor temperature is known
        if not has_sev_or_temp:
            sev_asked = case.is_question_already_asked("severity", norm_sym, "severity")
            if not sev_asked:
                q = f"On a scale of mild, moderate, or severe, how would you describe the intensity of your {norm_sym}?"
                return ClinicalGapResult(
                    is_complete=False,
                    missing_area="severity",
                    next_question=q,
                    clinical_justification=f"Severity of {norm_sym} is unknown; subjective intensity helps gauge severity and risk level.",
                    category="severity",
                    target_symptom=norm_sym,
                    target_field="severity",
                )

        # -------------------------------------------------------------
        # Area 4: Systematic Associated Symptoms Exploration
        # -------------------------------------------------------------
        associated_explored = case.is_question_already_asked("associated_symptoms", norm_sym, "associated_symptoms")

        if not associated_explored and not has_associated:
            if norm_sym == "fever":
                q = (
                    "Are you experiencing any other symptoms along with the fever, such as chills, "
                    "body aches, headache, cough, sore throat, nausea, vomiting, loose stools, or a rash?"
                )
                justification = (
                    "Evaluating presence or absence of respiratory, GI, and musculoskeletal symptoms "
                    "distinguishes viral syndromes, respiratory infections, gastrointestinal illnesses, and vector-borne conditions."
                )
            elif norm_sym == "headache":
                q = (
                    "Are you experiencing any nausea, sensitivity to light, neck stiffness, dizziness, "
                    "or fever along with the headache?"
                )
                justification = (
                    "Associated symptoms with headache differentiate tension headache, migraine, sinus congestion, "
                    "and intracranial or infectious red-flag conditions."
                )
            elif norm_sym == "weakness":
                q = (
                    "Along with the weakness, are you experiencing any fever, dizziness, shortness of breath, "
                    "poor appetite, or muscle aches?"
                )
                justification = "Explores whether weakness is part of an infectious, cardiorespiratory, or metabolic picture."
            else:
                q = f"Are you noticing any other symptoms or discomfort accompanying your {norm_sym}?"
                justification = f"Screening for associated symptoms to construct a clinical differential for {norm_sym}."

            return ClinicalGapResult(
                is_complete=False,
                missing_area="associated_symptoms",
                next_question=q,
                clinical_justification=justification,
                category="associated_symptoms",
                target_symptom=norm_sym,
                target_field="associated_symptoms",
            )

        # -------------------------------------------------------------
        # Area 5: Progression, Hydration, and Functional Stability
        # -------------------------------------------------------------
        progression_asked = case.is_question_already_asked("progression_hydration", None, "progression")
        has_progression = bool(case.progression.value)
        # Ask if progression/hydration unknown and we don't have enough clinical areas yet
        if not progression_asked and not has_progression and turn_id < 4:
            q = "Are your symptoms staying about the same, improving, or worsening, and have you been able to drink liquids and stay hydrated?"
            return ClinicalGapResult(
                is_complete=False,
                missing_area="progression_hydration",
                next_question=q,
                clinical_justification="Assessing symptom trajectory and hydration adequacy determines clinical stability and home safety.",
                category="progression_hydration",
                target_field="progression",
            )

        # -------------------------------------------------------------
        # Intake Criteria Met: 3–5 Key Areas Gathered
        # -------------------------------------------------------------
        logger.info(
            f"Intake clinical context satisfied for case (Primary: {primary_sym}, "
            f"Symptoms: {list(case.symptoms.keys())}, Turns: {case.turn_count})."
        )
        return ClinicalGapResult(
            is_complete=True,
            missing_area=None,
            next_question=None,
            clinical_justification="Sufficient clinical context gathered across core information areas for differential assessment.",
        )
