import datetime
import re
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FactStatus(str, Enum):
    NOT_ASKED = "not_asked"
    PROVIDED = "provided"
    UNKNOWN = "unknown"
    DECLINED = "declined"
    NOT_APPLICABLE = "not_applicable"
    CONFLICTING = "conflicting"


class FactProvenance(BaseModel):
    value: Any = None
    status: FactStatus = FactStatus.NOT_ASKED
    turn_id: Optional[int] = None
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    replaced_value: Optional[Any] = None


class SymptomRecord(BaseModel):
    """Detailed record of an individual reported symptom with its own duration, onset, severity, progression, and character."""
    name: str  # Clinical canonical entity name, e.g. "Weakness", "Headache", "Fever"
    original_wording: Optional[str] = None  # Exact user wording, e.g. "feeling weakness"
    normalized_name: str  # Lowercase key for lookup, e.g. "weakness"
    status: str = "present"  # "present", "absent", "unknown", "uncertain", "resolved"
    duration: Optional[str] = None  # e.g. "2 days"
    severity: Optional[str] = None  # e.g. "mild", "moderate", "severe", "7/10"
    onset: Optional[str] = None  # e.g. "yesterday"
    progression: Optional[str] = None  # e.g. "worsening", "improving", "constant"
    frequency: Optional[str] = None  # e.g. "intermittent", "continuous"
    triggers: Optional[str] = None
    relieving_factors: Optional[str] = None
    measured_value: Optional[str] = None  # e.g. "101 F" or "not measured"
    measurement_method: Optional[str] = None  # e.g. "thermometer", "subjective"
    first_turn_id: int = 1
    updated_turn_id: int = 1


class QuestionLedgerItem(BaseModel):
    """Audit ledger tracking what questions have been asked, answered, or declined."""
    category: str  # "primary_symptom", "symptom_duration", "symptom_severity", "associated_symptoms", "general"
    symptom: Optional[str] = None  # Normalized symptom key, e.g. "fever", "weakness"
    field: Optional[str] = None  # "duration", "severity", "primary_symptom"
    question_text: str = ""
    asked_turn: int = 1
    status: str = "pending"  # "pending", "answered", "declined"
    answered_turn: Optional[int] = None
    answer_value: Optional[str] = None


# Core canonical mappings for common symptoms, typos, and colloquial expressions
CANONICAL_SYMPTOM_MAP = {
    "weakness": "weakness",
    "weak": "weakness",
    "kamzori": "weakness",
    "weekness": "weakness",
    "lethargic": "fatigue",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "fatigue": "fatigue",
    "exhausted": "fatigue",
    "thakan": "fatigue",
    "fever": "fever",
    "feverish": "fever",
    "feever": "fever",
    "bukhar": "fever",
    "chills": "chills",
    "shivering": "chills",
    "headache": "headache",
    "headeche": "headache",
    "hedache": "headache",
    "head pain": "headache",
    "head hurting": "headache",
    "sir dard": "headache",
    "sar dard": "headache",
    "head in a vice grip": "headache",
    "vice grip": "headache",
    "tight band": "headache",
    "band around head": "headache",
    "band around my forehead": "headache",
    "worst headache of my life": "severe headache",
    "explosion in my brain": "severe headache",
    "thunderclap": "severe headache",
    "neck stiffening": "neck stiffness",
    "neck stiffness": "neck stiffness",
    "stiff neck": "neck stiffness",
    "nausea": "nausea",
    "nauseous": "nausea",
    "vomiting": "vomiting",
    "throwing up": "vomiting",
    "vomit": "vomiting",
    "ulti": "vomiting",
    "cough": "cough",
    "coughing": "cough",
    "khansi": "cough",
    "sore throat": "sore throat",
    "throat pain": "sore throat",
    "shortness of breath": "shortness of breath",
    "difficulty breathing": "shortness of breath",
    "breathlessness": "shortness of breath",
    "chest pain": "chest pain",
    "chest tightness": "chest pain",
    "abdominal pain": "abdominal pain",
    "stomach pain": "abdominal pain",
    "stomach ache": "abdominal pain",
    "belly pain": "abdominal pain",
    "pet dard": "abdominal pain",
    "dizziness": "dizziness",
    "dizzy": "dizziness",
    "chakkar": "dizziness",
    "body ache": "body ache",
    "body pain": "body ache",
    "muscle pain": "body ache",
    "badan dard": "body ache",
    "joint pain": "joint pain",
    "knee pain": "joint pain",
    "back pain": "back pain",
    "rash": "rash",
    "skin rash": "rash",
    "diarrhea": "diarrhea",
    "loose motions": "diarrhea",
    "loose stools": "diarrhea",
    "dast": "diarrhea",
}


class PatientCase(BaseModel):
    """Authoritative consolidated patient-case state for clinical symptom intake and memory."""
    # Primary/Initial presenting symptom
    primary_symptom: FactProvenance = Field(default_factory=FactProvenance)
    symptom_onset: FactProvenance = Field(default_factory=FactProvenance)
    duration: FactProvenance = Field(default_factory=FactProvenance)
    severity: FactProvenance = Field(default_factory=FactProvenance)
    progression: FactProvenance = Field(default_factory=FactProvenance)
    hydration_status: FactProvenance = Field(default_factory=FactProvenance)
    measured_temperature: Optional[str] = None
    
    # Detailed per-symptom dictionary: normalized_name -> SymptomRecord
    symptoms: Dict[str, SymptomRecord] = Field(default_factory=dict)

    # Lists for backward compatibility
    associated_symptoms: List[str] = Field(default_factory=list)
    denied_symptoms: List[str] = Field(default_factory=list)  # explicitly absent symptoms (e.g. no fever)
    unknown_symptoms: List[str] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    pregnancy_status: FactProvenance = Field(default_factory=FactProvenance)
    age_group: FactProvenance = Field(default_factory=FactProvenance)
    relevant_context: Optional[str] = None
    encounter_summary: Optional[str] = None
    safety_outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    intake_status: str = "in_progress"  # in_progress, complete, emergency

    # Question tracking and ledger
    pending_question: Optional[str] = None
    pending_field: Optional[str] = None
    pending_target: Optional[QuestionLedgerItem] = None
    question_ledger: List[QuestionLedgerItem] = Field(default_factory=list)
    asked_questions: List[str] = Field(default_factory=list)
    answered_questions: List[str] = Field(default_factory=list)
    declined_fields: List[str] = Field(default_factory=list)

    turn_count: int = 0
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @staticmethod
    def normalize_symptom_name(name: str) -> str:
        """Normalizes symptom descriptions to core canonical keywords, stripping sentence boilerplate."""
        if not name:
            return ""
        clean = name.lower().strip()

        # Check direct canonical keyword matches first
        for phrase, canonical in sorted(CANONICAL_SYMPTOM_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if re.search(rf"\b{re.escape(phrase)}\b", clean):
                return canonical

        # Strip conversational subjects, verbs and sentence prefixes
        clean = re.sub(
            r"\b(i am|i have had|i have|i'm having|i'm|im having|im|i feel|i've been having|i've been|ive been|having|feeling of|feeling|suffering from|experiencing|complaining of|got|started getting)\b",
            "",
            clean,
        )
        # Strip temporal and duration expressions
        clean = re.sub(
            r"\b(from last|from|for the last|for last|for|since|ago|\d+\s*(?:days?|hours?|weeks?|months?))\b",
            "",
            clean,
        )
        # Strip severity qualifiers and filler words
        clean = re.sub(
            r"\b(severe|mild|moderate|bad|terrible|slight|constant|throbbing|sharp|dull|chronic|acute|very|extremely|really|a bit of|some|lots of|lot of)\b",
            "",
            clean,
        )
        # Strip location prepositions
        clean = re.sub(r"\b(in my|in the|in|around|all over|of|with|body|my)\b", "", clean)
        clean = re.sub(r"[^\w\s]", " ", clean).strip()

        # After cleaning, check again against canonical dictionary
        for phrase, canonical in sorted(CANONICAL_SYMPTOM_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if re.search(rf"\b{re.escape(phrase)}\b", clean):
                return canonical

        tokens = [t for t in clean.split() if t and t not in {"a", "an", "the", "and", "or", "is", "was", "it"}]
        # Limit to max 3 words so sentences can never be symptom names
        return " ".join(tokens[:3]) if tokens else name.lower().strip()[:30]

    def add_or_update_symptom(
        self,
        name: str,
        status: str = "present",
        duration: Optional[str] = None,
        severity: Optional[str] = None,
        onset: Optional[str] = None,
        original_wording: Optional[str] = None,
        progression: Optional[str] = None,
        measured_value: Optional[str] = None,
        measurement_method: Optional[str] = None,
        turn_id: int = 1,
    ) -> SymptomRecord:
        """Adds or merges an individual symptom record into consolidated memory."""
        norm = self.normalize_symptom_name(name)
        if not norm:
            norm = name.lower().strip()

        # Clean display name: canonical capitalized entity, never a full sentence
        display_name = norm.title() if norm else name.strip()
        user_wording = original_wording or (name.strip() if len(name.split()) <= 4 else norm)

        # Find existing record by normalized key or exact match
        existing_key = None
        for k in self.symptoms.keys():
            if k == norm or norm in k or k in norm:
                existing_key = k
                break

        key = existing_key or norm
        if key in self.symptoms:
            rec = self.symptoms[key]
            rec.status = status
            if duration:
                rec.duration = duration
            if severity:
                rec.severity = severity
            if onset:
                rec.onset = onset
            if progression:
                rec.progression = progression
            if measured_value:
                rec.measured_value = measured_value
            if measurement_method:
                rec.measurement_method = measurement_method
            if original_wording:
                rec.original_wording = original_wording
            rec.updated_turn_id = turn_id
        else:
            rec = SymptomRecord(
                name=display_name,
                original_wording=user_wording,
                normalized_name=norm,
                status=status,
                duration=duration,
                severity=severity,
                onset=onset,
                progression=progression,
                measured_value=measured_value,
                measurement_method=measurement_method,
                first_turn_id=turn_id,
                updated_turn_id=turn_id,
            )
            self.symptoms[key] = rec

        # Synchronize backward-compatible primary_symptom
        if status == "present":
            if self.primary_symptom.status != FactStatus.PROVIDED or not self.primary_symptom.value:
                self.update_single_fact("primary_symptom", rec.name, FactStatus.PROVIDED, turn_id)
            elif rec.name.lower() != str(self.primary_symptom.value).lower():
                # Add to associated_symptoms list if not primary
                self.merge_list_items("associated_symptoms", [rec.name.lower()])

            if rec.duration and (not self.duration.value or self.primary_symptom.value == rec.name):
                self.update_single_fact("duration", rec.duration, FactStatus.PROVIDED, turn_id)

            if rec.severity and (not self.severity.value or self.primary_symptom.value == rec.name):
                self.update_single_fact("severity", rec.severity, FactStatus.PROVIDED, turn_id)

            if measured_value and norm == "fever":
                self.measured_temperature = measured_value
        elif status == "absent":
            self.merge_list_items("denied_symptoms", [rec.name.lower()])

        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return rec

    def get_symptom(self, name_or_norm: str) -> Optional[SymptomRecord]:
        """Looks up an existing symptom by raw or normalized name."""
        norm = self.normalize_symptom_name(name_or_norm)
        for k, rec in self.symptoms.items():
            if k == norm or norm in k or k in norm or rec.name.lower() == name_or_norm.lower():
                return rec
        return None

    def record_question_asked(
        self,
        category: str,
        question_text: str,
        symptom: Optional[str] = None,
        field: Optional[str] = None,
        turn_id: int = 1,
    ):
        """Records an asked question into the ledger and sets pending context."""
        item = QuestionLedgerItem(
            category=category,
            symptom=symptom,
            field=field,
            question_text=question_text,
            asked_turn=turn_id,
            status="pending",
        )
        self.question_ledger.append(item)
        self.pending_target = item
        self.pending_question = question_text
        self.pending_field = field or category

        lookup_key = f"{category}:{symptom or ''}:{field or ''}"
        if lookup_key not in self.asked_questions:
            self.asked_questions.append(lookup_key)
        if field and field not in self.asked_questions:
            self.asked_questions.append(field)

        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def resolve_pending_question(self, answer_value: str, turn_id: int = 1):
        """Marks the currently pending question as answered in the ledger."""
        if self.pending_target:
            self.pending_target.status = "answered"
            self.pending_target.answered_turn = turn_id
            self.pending_target.answer_value = answer_value

            lookup_key = f"{self.pending_target.category}:{self.pending_target.symptom or ''}:{self.pending_target.field or ''}"
            if lookup_key not in self.answered_questions:
                self.answered_questions.append(lookup_key)

        if self.pending_field and self.pending_field not in self.answered_questions:
            self.answered_questions.append(self.pending_field)

        self.pending_question = None
        self.pending_field = None
        self.pending_target = None
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def is_question_already_asked(self, category: str, symptom: Optional[str] = None, field: Optional[str] = None) -> bool:
        """Checks if an equivalent question was already asked or answered."""
        lookup_key = f"{category}:{symptom or ''}:{field or ''}"
        if lookup_key in self.asked_questions:
            return True
        for item in self.question_ledger:
            if item.category == category and item.symptom == symptom and item.field == field:
                return True
        return False

    def mark_field_declined_or_unknown(self, field_name: str, status: FactStatus = FactStatus.UNKNOWN, turn_id: int = 1):
        if field_name and field_name not in self.declined_fields:
            self.declined_fields.append(field_name)
        self.update_single_fact(field_name, None, status, turn_id)
        self.resolve_pending_question(answer_value="declined_or_unknown", turn_id=turn_id)

    def update_single_fact(self, field_name: str, new_value: Any, status: FactStatus, turn_id: int):
        """Updates a single scalar fact with provenance, replacing previous value if present."""
        current: FactProvenance = getattr(self, field_name, None)
        if current is None:
            return

        old_val = current.value if current.status == FactStatus.PROVIDED else None
        setattr(
            self,
            field_name,
            FactProvenance(
                value=new_value,
                status=status,
                turn_id=turn_id,
                updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                replaced_value=old_val if old_val != new_value else current.replaced_value,
            ),
        )
        if field_name not in self.answered_questions:
            self.answered_questions.append(field_name)
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def merge_list_items(self, list_field_name: str, new_items: List[str]):
        """Merges items into a list field preserving insertion order without duplicate entries."""
        if not new_items:
            return
        current_list: List[str] = getattr(self, list_field_name, [])
        for item in new_items:
            cleaned = item.strip().lower()
            if not any(existing.strip().lower() == cleaned for existing in current_list):
                current_list.append(item.strip())
        setattr(self, list_field_name, current_list)
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def remove_list_items(self, list_field_name: str, items_to_remove: List[str]):
        """Removes items from list field (e.g. if user later says 'actually no fever')."""
        if not items_to_remove:
            return
        current_list: List[str] = getattr(self, list_field_name, [])
        remove_set = {r.strip().lower() for r in items_to_remove}
        filtered = [x for x in current_list if x.strip().lower() not in remove_set]
        setattr(self, list_field_name, filtered)
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_summary_dict(self) -> Dict[str, Any]:
        """Provides a clean dictionary of confirmed patient facts for RAG, safety, and evaluation."""
        symptoms_map = {}
        for k, v in self.symptoms.items():
            symptoms_map[k] = {
                "name": v.name,
                "status": v.status,
                "duration": v.duration,
                "severity": v.severity,
                "onset": v.onset,
                "progression": v.progression,
                "measured_value": v.measured_value,
            }

        return {
            "primary_symptom": self.primary_symptom.value,
            "symptom_onset": self.symptom_onset.value,
            "duration": self.duration.value,
            "severity": self.severity.value,
            "progression": self.progression.value,
            "measured_temperature": self.measured_temperature,
            "symptoms": symptoms_map,
            "associated_symptoms": [s.lower() for s in self.associated_symptoms],
            "denied_symptoms": [s.lower() for s in self.denied_symptoms],
            "unknown_symptoms": [s.lower() for s in self.unknown_symptoms],
            "medical_history": list(self.medical_history),
            "medications": list(self.medications),
            "allergies": list(self.allergies),
            "risk_factors": list(self.risk_factors),
            "pregnancy_status": self.pregnancy_status.value,
            "age_group": self.age_group.value,
            "intake_status": self.intake_status,
        }
