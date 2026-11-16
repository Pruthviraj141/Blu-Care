import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmergencyRule(BaseModel):
    id: str
    description: str
    keywords: List[str]
    severity_level: str = "critical"
    instruction: str


# Configurable provisional emergency red-flag ruleset
PROVISIONAL_EMERGENCY_RULES: List[EmergencyRule] = [
    EmergencyRule(
        id="EMERGENCY-CHEST-PAIN",
        description="Crushing chest pain radiating to arm, jaw, or shortness of breath",
        keywords=["chest pain", "pressure in chest", "tightness in chest", "radiating to jaw", "radiating to left arm", "heart attack"],
        instruction="Call your local emergency services (e.g. 911, 999, 112) or go to the nearest emergency room immediately.",
    ),
    EmergencyRule(
        id="EMERGENCY-STROKE-FAST",
        description="Signs of stroke: sudden facial drooping, arm weakness, speech difficulty",
        keywords=["facial drooping", "face drooping", "arm weakness", "slurred speech", "sudden numbness one side", "cant speak"],
        instruction="These symptoms may indicate a stroke. Seek emergency medical attention immediately.",
    ),
    EmergencyRule(
        id="EMERGENCY-SEVERE-RESPIRATORY",
        description="Acute respiratory distress, choking, or inability to breathe",
        keywords=["cannot breathe", "struggling to breathe", "gasping for air", "severe shortness of breath", "turning blue", "lips blue"],
        instruction="Severe breathing difficulty requires immediate emergency medical care. Call emergency services now.",
    ),
    EmergencyRule(
        id="EMERGENCY-ANAPHYLAXIS",
        description="Signs of severe allergic reaction / anaphylaxis",
        keywords=["throat closing", "swollen tongue", "swollen throat", "anaphylaxis", "cannot swallow air"],
        instruction="If you have an epinephrine auto-injector (EpiPen), use it now and call emergency services immediately.",
    ),
    EmergencyRule(
        id="EMERGENCY-THUNDERCLAP-HEADACHE",
        description="Sudden severe headache reaching peak intensity within seconds",
        keywords=["worst headache of my life", "thunderclap headache", "sudden severe headache with stiff neck"],
        instruction="A sudden, severe headache of maximum intensity requires urgent medical evaluation at an emergency department.",
    ),
]


class SafetyEvaluationResult(BaseModel):
    is_emergency: bool = False
    rule_id: Optional[str] = None
    ruleset_version: str = Field(default_factory=lambda: settings.safety_ruleset_version)
    outcome: str = "no_emergency_detected"  # no_emergency_detected, emergency_detected, safety_review_required
    emergency_message: Optional[str] = None


class SafetyEngine:
    """Independent deterministic emergency detection engine running on every conversation turn."""

    @classmethod
    def evaluate(
        cls,
        user_message: str,
        primary_symptom: Optional[str] = None,
        associated_symptoms: Optional[List[str]] = None,
    ) -> SafetyEvaluationResult:
        if not user_message:
            return SafetyEvaluationResult()

        text_to_scan = user_message.lower()
        if primary_symptom:
            text_to_scan += f" {primary_symptom.lower()}"
        if associated_symptoms:
            text_to_scan += " " + " ".join(s.lower() for s in associated_symptoms)

        for rule in PROVISIONAL_EMERGENCY_RULES:
            for kw in rule.keywords:
                if kw in text_to_scan:
                    logger.warning(f"EMERGENCY RULE TRIGGERED: {rule.id} on keyword '{kw}'")
                    msg = (
                        f"🚨 **EMERGENCY WARNING: Immediate Medical Attention Required**\n\n"
                        f"{rule.instruction}\n\n"
                        f"Please do not wait for an online assessment. If you are experiencing {rule.description}, "
                        f"call your local emergency number (such as 911, 999, or 112) or go to the nearest emergency room immediately."
                    )
                    return SafetyEvaluationResult(
                        is_emergency=True,
                        rule_id=rule.id,
                        ruleset_version=settings.safety_ruleset_version,
                        outcome="emergency_detected",
                        emergency_message=msg,
                    )

        return SafetyEvaluationResult(
            is_emergency=False,
            outcome="no_emergency_detected",
        )
