import logging
import json
import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class ExtractedSymptomEntity(BaseModel):
    name: str = Field(description="Normalized clinical symptom name, e.g. 'weakness', 'fever', 'headache'")
    original_wording: Optional[str] = Field(default=None, description="Exact phrase spoken by patient, e.g. 'feeling weakness'")
    duration: Optional[str] = Field(default=None, description="Duration specific to this symptom if stated, e.g. '2 days'")
    severity: Optional[str] = Field(default=None, description="Severity specific to this symptom, e.g. 'mild'")
    status: str = Field(default="present", description="'present' or 'absent'")


class ExtractedSymptoms(BaseModel):
    primary_symptom: Optional[str] = None
    original_wording: Optional[str] = None
    symptom_onset: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None  # e.g. "6/10", "mild", "severe"
    symptoms: List[ExtractedSymptomEntity] = Field(default_factory=list)
    associated_symptoms: List[str] = Field(default_factory=list)
    denied_symptoms: List[str] = Field(default_factory=list)  # explicitly absent (e.g. "no fever", "not vomiting")
    medical_history: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    is_correction: bool = False
    corrected_field: Optional[str] = None
    user_declined_or_unknown: List[str] = Field(default_factory=list)


EXTRACTION_SYSTEM_PROMPT = """Extract clinical triage facts from the patient's message into valid JSON.

CRITICAL CLINICAL RULES:
1. Normalize symptoms to standard clinical terms (e.g. "headache", "weakness", "fever", "nausea", "cough", "abdominal pain", "diarrhea", "dizziness", "fatigue").
2. Support grammar mistakes, misspellings ("headeche" -> "headache", "feever" -> "fever", "weekness" -> "weakness") and Hinglish ("sir dard" -> "headache", "pet dard" -> "abdominal pain", "chakkar" -> "dizziness", "bukhar" -> "fever", "kamzori" -> "weakness", "thakan" -> "fatigue", "ulti" -> "vomiting", "dast" -> "diarrhea").
3. NEVER use an entire patient sentence or conversational phrase as a symptom name. For example, for "I am feeling weakness from 2 days", primary_symptom is "weakness", original_wording is "feeling weakness", duration is "2 days".
4. Extract multiple symptoms with individual durations if mentioned (e.g. "fever for 3 days and weakness since yesterday" -> two distinct symptoms).
5. If user denies symptoms (e.g. "no fever", "not vomiting"), add to denied_symptoms.
6. Return ONLY valid JSON matching this schema:
{
  "primary_symptom": string or null,
  "original_wording": string or null,
  "duration": string or null,
  "severity": string or null,
  "symptoms": [
    {
      "name": string,
      "original_wording": string or null,
      "duration": string or null,
      "severity": string or null,
      "status": "present" or "absent"
    }
  ],
  "associated_symptoms": [string],
  "denied_symptoms": [string],
  "medical_history": [string],
  "medications": [string],
  "is_correction": boolean,
  "corrected_field": string or null,
  "user_declined_or_unknown": [string]
}
"""


class SymptomExtractor:
    """Extracts structured medical intake data from patient messages with fail-safe fallbacks."""

    @classmethod
    def extract(cls, user_message: str, current_facts: Optional[Dict[str, Any]] = None) -> ExtractedSymptoms:
        if not user_message or not user_message.strip():
            return ExtractedSymptoms()

        llm = get_llm()
        context_prompt = ""
        if current_facts:
            context_prompt = f"\nCurrently known facts: {json.dumps(current_facts)}"

        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=f"Patient Message: \"{user_message}\"{context_prompt}"),
        ]

        try:
            response = llm.invoke(messages)
            content = getattr(response, "content", "")
            if not isinstance(content, str):
                content = str(content)

            # Strip markdown json blocks if returned
            clean_json = content.strip()
            if "```" in clean_json:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_json)
                if match:
                    clean_json = match.group(1).strip()

            parsed = json.loads(clean_json)
            extracted = ExtractedSymptoms(**parsed)
            if extracted.symptom_onset and not extracted.duration:
                extracted.duration = extracted.symptom_onset
            return extracted
        except Exception as e:
            logger.warning(f"Structured extraction LLM call failed or produced invalid JSON ({e}). Using deterministic heuristics.")
            return cls._heuristic_fallback(user_message)

    @classmethod
    def _heuristic_fallback(cls, message: str) -> ExtractedSymptoms:
        """Lightweight regex/keyword fallback when LLM is unreachable or returns malformed text."""
        msg = message.lower()
        extracted = ExtractedSymptoms()

        # Severity check
        sev_match = re.search(r"(\d{1,2})\s*/\s*10", msg)
        if sev_match:
            extracted.severity = f"{sev_match.group(1)}/10"
        elif "severe" in msg:
            extracted.severity = "severe"
        elif "mild" in msg:
            extracted.severity = "mild"
        elif "moderate" in msg:
            extracted.severity = "moderate"

        # Duration check
        dur_match = re.search(
            r"(since\s+\w+|from\s+last\s+\w+\s*(?:days?|hours?|weeks?|months?)|from\s+\d+\s*(?:days?|hours?|weeks?|months?)|for\s+(?:last\s+)?\w+\s*(?:days?|hours?|weeks?|months?)|\d+\s*(?:days?|hours?|weeks?)\s*ago|yesterday|\w+\s*(?:days?|hours?|weeks?))",
            msg,
        )
        if dur_match:
            extracted.duration = dur_match.group(1)

        # Denied symptoms
        if "no fever" in msg or "without fever" in msg:
            extracted.denied_symptoms.append("fever")
        if "no vomiting" in msg or "not vomiting" in msg:
            extracted.denied_symptoms.append("vomiting")
        if "no nausea" in msg:
            extracted.denied_symptoms.append("nausea")

        # General negative answers for associated symptoms question (e.g. "no", "none", "nothing else")
        clean_msg = re.sub(r"[^\w\s]", "", msg).strip()
        if clean_msg in ("no", "none", "nope", "nothing", "no other symptoms", "nothing else", "not really", "no others", "no more"):
            extracted.denied_symptoms.append("none_reported")

        # Unknown / decline answers
        if any(phrase in msg for phrase in ("dont know", "don't know", "not sure", "cant tell", "can't tell", "skip", "prefer not to say", "no idea")):
            extracted.user_declined_or_unknown.append("pending")

        # Basic primary symptom recognition for offline fallback
        common_symptoms = [
            ("throbbing headache", "headache"),
            ("severe headache", "headache"),
            ("headache", "headache"),
            ("head pain", "headache"),
            ("sir dard", "headache"),
            ("sar dard", "headache"),
            ("chest pain", "chest pain"),
            ("shortness of breath", "shortness of breath"),
            ("difficulty breathing", "shortness of breath"),
            ("abdominal pain", "abdominal pain"),
            ("stomach pain", "abdominal pain"),
            ("stomach ache", "abdominal pain"),
            ("pet dard", "abdominal pain"),
            ("back pain", "back pain"),
            ("cough", "cough"),
            ("khansi", "cough"),
            ("sore throat", "sore throat"),
            ("dizziness", "dizziness"),
            ("chakkar", "dizziness"),
            ("fatigue", "fatigue"),
            ("thakan", "fatigue"),
            ("weakness", "weakness"),
            ("kamzori", "weakness"),
            ("fever", "fever"),
            ("bukhar", "fever"),
            ("rash", "rash"),
            ("nausea", "nausea"),
            ("vomiting", "vomiting"),
            ("ulti", "vomiting"),
            ("diarrhea", "diarrhea"),
            ("loose motions", "diarrhea"),
        ]
        for pattern, canonical in common_symptoms:
            if re.search(rf"\b{re.escape(pattern)}\b", msg) and not any(den in msg for den in [f"no {pattern}", f"without {pattern}", f"not {pattern}"]):
                extracted.primary_symptom = canonical
                extracted.original_wording = pattern
                extracted.symptoms.append(
                    ExtractedSymptomEntity(
                        name=canonical,
                        original_wording=pattern,
                        duration=extracted.duration,
                        severity=extracted.severity,
                        status="present",
                    )
                )
                break

        # Corrections
        if "actually" in msg or "correction" in msg or "not yesterday" in msg:
            extracted.is_correction = True
            if dur_match:
                extracted.corrected_field = "duration"

        return extracted

