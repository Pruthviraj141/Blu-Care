import logging
import re
from typing import Optional, Tuple, List, Dict, Any

from app.services.patient_case import PatientCase, SymptomRecord, FactStatus

logger = logging.getLogger(__name__)

COMMON_SYMPTOM_PATTERNS = [
    ("feeling very weak", "weakness"),
    ("feeling weakness", "weakness"),
    ("feeling weak", "weakness"),
    ("feel weak", "weakness"),
    ("weakness in body", "weakness"),
    ("body weakness", "weakness"),
    ("weakness", "weakness"),
    ("weekness", "weakness"),
    ("kamzori", "weakness"),
    ("weak", "weakness"),
    ("feeling tired", "fatigue"),
    ("feel tired", "fatigue"),
    ("feeling exhausted", "fatigue"),
    ("fatigue", "fatigue"),
    ("tiredness", "fatigue"),
    ("thakan", "fatigue"),
    ("tired", "fatigue"),
    ("feeling sick", "nausea"),
    ("nauseous", "nausea"),
    ("nausea", "nausea"),
    ("throwing up", "vomiting"),
    ("vomiting", "vomiting"),
    ("vomit", "vomiting"),
    ("ulti", "vomiting"),
    ("high fever", "fever"),
    ("mild fever", "fever"),
    ("feeling feverish", "fever"),
    ("feverish", "fever"),
    ("feever", "fever"),
    ("bukhar", "fever"),
    ("fever", "fever"),
    ("head hurting", "headache"),
    ("head hurts", "headache"),
    ("head pain", "headache"),
    ("throbbing headache", "headache"),
    ("severe headache", "headache"),
    ("worst headache of my life", "severe headache"),
    ("explosion in my brain", "severe headache"),
    ("thunderclap headache", "severe headache"),
    ("head in a vice grip", "headache"),
    ("vice grip", "headache"),
    ("tight band around my forehead", "headache"),
    ("tight band around forehead", "headache"),
    ("tight band", "headache"),
    ("band around my forehead", "headache"),
    ("band around head", "headache"),
    ("headache", "headache"),
    ("sir dard", "headache"),
    ("sar dard", "headache"),
    ("neck stiffening", "neck stiffness"),
    ("neck stiffness", "neck stiffness"),
    ("stiff neck", "neck stiffness"),
    ("sore throat", "sore throat"),
    ("throat pain", "sore throat"),
    ("shortness of breath", "shortness of breath"),
    ("difficulty breathing", "shortness of breath"),
    ("chest pain", "chest pain"),
    ("stomach pain", "abdominal pain"),
    ("abdominal pain", "abdominal pain"),
    ("stomach ache", "abdominal pain"),
    ("belly pain", "abdominal pain"),
    ("pet dard", "abdominal pain"),
    ("dizziness", "dizziness"),
    ("feeling dizzy", "dizziness"),
    ("chakkar", "dizziness"),
    ("dizzy", "dizziness"),
    ("coughing", "cough"),
    ("khansi", "cough"),
    ("cough", "cough"),
    ("chills", "chills"),
    ("shivering", "chills"),
    ("body ache", "body ache"),
    ("body pain", "body ache"),
    ("badan dard", "body ache"),
    ("body aches", "body ache"),
    ("muscle pain", "body ache"),
    ("joint pain", "joint pain"),
    ("rash", "rash"),
    ("diarrhea", "diarrhea"),
    ("loose motions", "diarrhea"),
    ("loose stools", "diarrhea"),
    ("dast", "diarrhea"),
]


class PatientLookupEngine:
    """Deterministic patient context lookup and question selection layer."""

    @classmethod
    def check_already_recorded_symptom(cls, message: str, case: PatientCase, turn_id: int) -> Optional[str]:
        """
        Detects if the user repeated an already known and assessed symptom (e.g. 'fever').
        Returns an acknowledgment + next question without repeating duration question.
        """
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()
        if cls.extract_duration_string(message) or cls.extract_severity_string(message):
            return None

        # Check for clean match against known symptoms
        for pattern, canonical in sorted(COMMON_SYMPTOM_PATTERNS, key=lambda x: len(x[0]), reverse=True):
            if re.fullmatch(rf"(i have|still have|having|just)?\s*{pattern}\s*(too|also)?", msg_lower) or msg_lower == pattern or msg_lower == canonical:
                rec = case.get_symptom(canonical) or case.get_symptom(pattern)
                if rec and rec.status == "present" and rec.duration:
                    # This symptom is already registered with duration
                    is_complete, next_q = cls.select_next_adaptive_question(case, turn_id=turn_id)
                    ack = f"I have already recorded your {rec.name} lasting {rec.duration}."
                    if next_q:
                        return f"{ack} {next_q}"
                    return ack
        return None

    @staticmethod
    def check_greeting(message: str, case: PatientCase) -> Optional[str]:
        """Detects simple conversational greetings without invoking an LLM."""
        msg = message.lower().strip()
        cleaned = re.sub(r"[^\w\s]", "", msg).strip()
        greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "hi there", "hello there"}
        if cleaned in greetings:
            # If no symptoms are recorded yet, prompt for the primary symptom
            if not case.symptoms and (not case.primary_symptom.value or case.primary_symptom.status != FactStatus.PROVIDED):
                return "Hello! What is the main symptom or discomfort you are experiencing?"
        return None

    @staticmethod
    def extract_duration_string(text: str) -> Optional[str]:
        """Extracts standard duration patterns from text, supporting both digits and number words."""
        msg = text.lower().strip()
        num_pattern = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a\s+few|several|a)"
        dur_match = re.search(
            rf"(\b{num_pattern}\s+(?:days?|hours?|weeks?|months?)\b|\bfrom\s+last\s+{num_pattern}\s*(?:days?|hours?|weeks?|months?)|\blast\s+{num_pattern}\s*(?:days?|hours?|weeks?|months?)|\bsince\s+[a-z0-9\s]+\b|\byesterday\b|\btoday\b)",
            msg,
        )
        if dur_match:
            raw = dur_match.group(0).strip()
            cleaned = re.sub(r"^(from\s+last\s+|last\s+|for\s+|from\s+)", "", raw).strip()
            return cleaned or raw
        
        # Numbers with units like "3 days", "2 weeks", "three days"
        tokens = msg.split()
        if len(tokens) <= 3 and any(u in msg for u in ["day", "hour", "week", "month"]):
            return text.strip()
        return None

    @staticmethod
    def extract_severity_string(text: str) -> Optional[str]:
        """Extracts standard pain scale or severity classifications."""
        msg = text.lower().strip()
        scale_match = re.search(r"(\b\d{1,2}\s*/\s*10\b)", msg)
        if scale_match:
            return scale_match.group(0).strip()
        for sev in ["severe", "moderate", "mild", "bad", "terrible", "intense", "excruciating", "slight"]:
            if re.search(rf"\b{sev}\b", msg):
                return sev
        return None

    @staticmethod
    def extract_measured_temperature(text: str) -> Optional[str]:
        """Extracts numerical body temperature readings in Fahrenheit or Celsius."""
        msg = text.lower().strip()
        temp_match = re.search(r"(\b\d{2,3}(?:\.\d)?)\s*(?:°\s*[fc]|deg(?:rees)?\s*[fc]?|[fc]\b)", msg)
        if temp_match:
            return temp_match.group(0).strip()
        num_match = re.search(r"\b(9[7-9](?:\.\d)?|10[0-6](?:\.\d)?|3[6-9](?:\.\d)?|4[0-2](?:\.\d)?)\b", msg)
        if num_match:
            val = float(num_match.group(1))
            unit = "°C" if val < 45 else "°F"
            return f"{val} {unit}"
        return None

    @classmethod
    def try_deterministic_answer(cls, message: str, case: PatientCase, turn_id: int) -> bool:
        """
        Evaluates the message against the currently pending question.
        Returns True if the pending question was deterministically answered.
        """
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()

        # Case 0: Explicit Correction Pattern (e.g., "Actually, it started 3 days ago")
        if re.search(r"\b(actually|correction|i meant|mistake|sorry)\b", msg_lower):
            dur = cls.extract_duration_string(message)
            sev = cls.extract_severity_string(message)
            if dur:
                target_sym = None
                for pattern, canonical in COMMON_SYMPTOM_PATTERNS:
                    if re.search(rf"\b{pattern}\b", msg_lower):
                        target_sym = pattern
                        break
                if not target_sym and case.primary_symptom.value:
                    target_sym = str(case.primary_symptom.value)
                if target_sym:
                    case.add_or_update_symptom(name=target_sym, duration=dur, turn_id=turn_id)
                case.update_single_fact("duration", dur, FactStatus.PROVIDED, turn_id=turn_id)
                case.resolve_pending_question(answer_value=dur, turn_id=turn_id)
                return True
            if sev:
                target_sym = str(case.primary_symptom.value) if case.primary_symptom.value else None
                if target_sym:
                    case.add_or_update_symptom(name=target_sym, severity=sev, turn_id=turn_id)
                case.update_single_fact("severity", sev, FactStatus.PROVIDED, turn_id=turn_id)
                case.resolve_pending_question(answer_value=sev, turn_id=turn_id)
                return True

        if not case.pending_target:
            return False

        target = case.pending_target

        # Case A: Pending question was primary symptom
        if target.category == "primary_symptom":
            matched_sym = None
            for pattern, canonical in sorted(COMMON_SYMPTOM_PATTERNS, key=lambda x: len(x[0]), reverse=True):
                if re.search(rf"\b{pattern}\b", message.lower()):
                    matched_sym = canonical
                    break
            symptom_name = matched_sym or case.normalize_symptom_name(msg_clean)
            dur = cls.extract_duration_string(message)
            sev = cls.extract_severity_string(message)
            case.add_or_update_symptom(name=symptom_name, status="present", duration=dur, severity=sev, turn_id=turn_id)
            case.resolve_pending_question(answer_value=symptom_name, turn_id=turn_id)
            return True

        # Case B: Pending question was symptom duration
        if target.category == "symptom_duration":
            dur = cls.extract_duration_string(message)
            if dur:
                target_sym = target.symptom or (case.primary_symptom.value if case.primary_symptom else None)
                if target_sym:
                    case.add_or_update_symptom(name=target_sym, duration=dur, turn_id=turn_id)
                case.resolve_pending_question(answer_value=dur, turn_id=turn_id)
                return True

        # Case C: Pending question was symptom severity
        if target.category in ("symptom_severity", "severity"):
            sev = cls.extract_severity_string(message)
            if sev:
                target_sym = target.symptom or (case.primary_symptom.value if case.primary_symptom else None)
                if target_sym:
                    case.add_or_update_symptom(name=target_sym, severity=sev, turn_id=turn_id)
                case.update_single_fact("severity", sev, FactStatus.PROVIDED, turn_id=turn_id)
                case.resolve_pending_question(answer_value=sev, turn_id=turn_id)
                return True

        # Case D: Pending question was measured temperature
        if target.category == "measured_temperature":
            temp = cls.extract_measured_temperature(message)
            sev = cls.extract_severity_string(message)
            if temp:
                case.measured_temperature = temp
                case.add_or_update_symptom("fever", measured_value=temp, severity=sev, turn_id=turn_id)
                case.resolve_pending_question(answer_value=temp, turn_id=turn_id)
                return True
            # Check for subjective severity or statement that it wasn't measured with thermometer
            if sev or any(w in msg_lower for w in ["mild", "moderate", "high", "haven't", "havent", "didn't", "didnt", "no thermometer", "not measured", "not checked"]):
                val = f"Subjective ({sev or 'mild'})"
                case.measured_temperature = val
                case.add_or_update_symptom("fever", severity=sev or "mild", measured_value=val, turn_id=turn_id)
                case.resolve_pending_question(answer_value=val, turn_id=turn_id)
                return True

        # Case E: Pending question was progression / hydration
        if target.category == "progression_hydration":
            prog = None
            if any(w in msg_lower for w in ["worse", "worsening", "increasing", "more severe"]):
                prog = "worsening"
            elif any(w in msg_lower for w in ["better", "improving", "subsiding", "less"]):
                prog = "improving"
            elif any(w in msg_lower for w in ["same", "constant", "unchanged", "staying"]):
                prog = "constant"

            hydration = "adequate" if any(w in msg_lower for w in ["water", "fluid", "drinking", "hydrate", "liquids"]) and not any(w in msg_lower for w in ["can't", "cannot", "unable"]) else None
            if prog:
                case.update_single_fact("progression", prog, FactStatus.PROVIDED, turn_id=turn_id)
            if hydration:
                case.update_single_fact("hydration_status", hydration, FactStatus.PROVIDED, turn_id=turn_id)

            case.resolve_pending_question(answer_value=prog or msg_clean, turn_id=turn_id)
            return True

        # Case F: Pending question was symptom character / distribution
        if target.category == "symptom_character":
            target_sym = target.symptom or (case.primary_symptom.value if case.primary_symptom else None)
            sev = cls.extract_severity_string(message)
            if target_sym:
                case.add_or_update_symptom(str(target_sym), original_wording=msg_clean, severity=sev, turn_id=turn_id)
            if sev:
                case.update_single_fact("severity", sev, FactStatus.PROVIDED, turn_id=turn_id)
            case.resolve_pending_question(answer_value=msg_clean, turn_id=turn_id)
            return True

        # Case G: Pending question was associated symptoms
        if target.category == "associated_symptoms":
            case.resolve_pending_question(answer_value=msg_clean, turn_id=turn_id)
            return True

        # Case H: Pending question was medical history / medications
        if target.category == "medical_history":
            if any(neg in msg_clean.lower() for neg in ["no", "none", "nothing", "nil", "healthy", "nope", "not taking"]):
                case.medical_history = ["none"]
                case.medications = ["none"]
                case.resolve_pending_question(answer_value="none", turn_id=turn_id)
                return True
            else:
                case.medical_history = [msg_clean]
                case.resolve_pending_question(answer_value=msg_clean, turn_id=turn_id)
                return True

        return False

    @classmethod
    def inspect_and_merge_new_symptoms(cls, message: str, case: PatientCase, turn_id: int) -> bool:
        """
        Scans incoming text for newly mentioned symptoms, negative statements, and durations.
        Splits by clauses to attach durations and severities accurately without cross-contamination.
        Merges new facts into consolidated patient memory.
        """
        msg_lower = message.lower()
        found_any = False

        # Split message into clauses to associate durations and severities with individual symptoms
        clauses = re.split(r"[,;]|\band\b", message)

        matched_canonicals = set()

        negation_pattern = r"\b(no|without|not|denies|free of|never had|don't have|dont have|haven't had|havent had|neither)\b"
        affirmative_reset_pattern = r"\b(with|but|also|however|having|started|and i have|and i am|accompanied by)\b"

        in_negation_scope = False
        for clause in clauses:
            clause_lower = clause.lower().strip()
            if not clause_lower:
                continue

            clause_dur = cls.extract_duration_string(clause)
            clause_sev = cls.extract_severity_string(clause)

            # Check if this clause resets negation to affirmative
            if re.search(affirmative_reset_pattern, clause_lower):
                in_negation_scope = False

            # Check if this clause contains an explicit negation operator
            neg_match = re.search(negation_pattern, clause_lower)
            if neg_match:
                in_negation_scope = True
                neg_start = neg_match.start()
            else:
                neg_start = -1

            for pattern, canonical in sorted(COMMON_SYMPTOM_PATTERNS, key=lambda x: len(x[0]), reverse=True):
                if canonical in matched_canonicals:
                    continue
                match = re.search(rf"\b{re.escape(pattern)}\b", clause_lower)
                if match:
                    matched_canonicals.add(canonical)
                    # If symptom appeared before the negation word in this same clause, it is positive
                    if neg_start != -1 and match.start() < neg_start:
                        is_negated = False
                    else:
                        is_negated = in_negation_scope

                    if is_negated:
                        case.add_or_update_symptom(name=canonical, status="absent", turn_id=turn_id)
                    else:
                        case.add_or_update_symptom(
                            name=canonical,
                            status="present",
                            duration=clause_dur,
                            severity=clause_sev,
                            turn_id=turn_id,
                        )
                    found_any = True

        # If only a single symptom was identified across the entire message, allow whole-message duration/severity
        if len(matched_canonicals) == 1:
            sym_key = next(iter(matched_canonicals))
            rec = case.get_symptom(sym_key)
            if rec and rec.status == "present":
                if not rec.duration:
                    rec.duration = cls.extract_duration_string(message)
                if not rec.severity:
                    rec.severity = cls.extract_severity_string(message)

        return found_any

    @classmethod
    def select_next_adaptive_question(
        cls,
        case: PatientCase,
        turn_id: int,
        candidate_conditions: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Uses QuestionPlanner to evaluate clinical information gaps and select
        the next highest-yield question. Records question in ledger.
        """
        from app.services.question_planner import QuestionPlanner
        gap = QuestionPlanner.evaluate_clinical_gap(case, turn_id=turn_id, candidate_conditions=candidate_conditions)
        if gap.is_complete or not gap.next_question:
            return True, None

        case.record_question_asked(
            category=gap.category or "clinical_inquiry",
            question_text=gap.next_question,
            symptom=gap.target_symptom,
            field=gap.target_field,
            turn_id=turn_id,
        )
        return False, gap.next_question
