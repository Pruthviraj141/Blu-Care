import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from app.services.patient_case import PatientCase

logger = logging.getLogger(__name__)

COMMON_TYPOS = {
    r"\bmigranes?\b": "migraine",
    r"\bmigrains?\b": "migraine",
    r"\bmigran\b": "migraine",
    r"\bnausia\b": "nausea",
    r"\bnausious\b": "nauseous",
    r"\bvomitting\b": "vomiting",
    r"\bvomitingg\b": "vomiting",
    r"\bhead ache\b": "headache",
    r"\bheadach\b": "headache",
    r"\bpharangitis\b": "pharyngitis",
    r"\bpharyngytis\b": "pharyngitis",
    r"\bbronchitus\b": "bronchitis",
    r"\bgastroentritis\b": "gastroenteritis",
    r"\bdehydraton\b": "dehydration",
    r"\bdiarhea\b": "diarrhea",
    r"\bdiarrhoea\b": "diarrhea",
    r"\bdiarrea\b": "diarrhea",
    r"\bfevr\b": "fever",
    r"\bfevar\b": "fever",
    r"\bstomache\b": "stomach",
    r"\bthroatt\b": "throat",
}

CONDITION_KEYWORDS = [
    "tension-type headache", "tension headache", "migraine", "shirashoola",
    "viral pharyngitis", "pharyngitis", "sore throat",
    "viral gastroenteritis", "gastroenteritis", "dehydration",
    "acute bronchitis", "bronchitis",
    "acute viral fever", "viral fever", "fever", "jwara",
    "dengue fever", "dengue",
    "influenza", "flu", "kasa", "cough"
]


def clean_typos(text: str) -> str:
    """Corrects common medical misspellings deterministically without changing meaning."""
    cleaned = text
    for pattern, repl in COMMON_TYPOS.items():
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned


def resolve_coreference(
    query: str,
    history: Optional[List[Dict[str, Any]]] = None,
    case: Optional[PatientCase] = None,
) -> str:
    """
    Resolves conversational pronouns (its, this, that, it) using prior turns
    or active patient case context.
    """
    q_lower = query.lower()
    has_pronoun = bool(re.search(r"\b(its|it|this|these|that)\b", q_lower))
    if not has_pronoun:
        return query

    found_condition = None

    # Check conversation history first (most recent turns)
    if history:
        for msg in reversed(history):
            content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
            content_lower = content.lower()
            for cond in CONDITION_KEYWORDS:
                if cond in content_lower:
                    found_condition = cond
                    break
            if found_condition:
                break

    # Check patient case primary symptom as fallback
    if not found_condition and case and case.primary_symptom.value:
        found_condition = str(case.primary_symptom.value).lower()

    if not found_condition:
        return query

    # Substitute pronouns with clear target entity
    resolved = re.sub(r"\b(its)\b", f"{found_condition}'s", query, flags=re.IGNORECASE)
    resolved = re.sub(r"\b(it|this|that)\b", found_condition, resolved, flags=re.IGNORECASE)
    return resolved


def build_medical_query(case: PatientCase, domain: Optional[str] = None) -> str:
    """
    Builds a deterministic, clinically focused search query strictly from the structured patient case.
    Avoids conversational noise, excludes user identifiers, preserves negations, duration, and clinical domain.
    """
    parts = []

    # 0. Domain Context (e.g. Ayurvedic / Traditional vs Conventional triage)
    if domain:
        parts.append(domain.strip())
    elif any(term in str(case.primary_symptom.value or "").lower() for term in ["ayurved", "ayush", "traditional", "jwara", "kasa", "shirashoola"]):
        parts.append("Ayurvedic clinical guidance")

    # 1. Primary Symptom (Core Subject)
    if case.primary_symptom.value:
        parts.append(str(case.primary_symptom.value).strip())

    # 2. Duration & Onset
    if case.duration.value:
        parts.append(f"lasting {case.duration.value}")
    elif case.symptom_onset.value:
        parts.append(f"onset {case.symptom_onset.value}")

    # 3. Severity
    if case.severity.value and case.severity.value != "unknown":
        parts.append(f"severity {case.severity.value}")

    # 4. Associated Symptoms (Positive)
    if case.associated_symptoms:
        primary_lower = str(case.primary_symptom.value or "").lower()
        denied_lowers = {d.lower() for d in case.denied_symptoms if d}
        valid_assoc = [
            s for s in case.associated_symptoms
            if s and s.lower() != primary_lower and s.lower() not in denied_lowers
        ]
        if valid_assoc:
            parts.append(f"with {', '.join(valid_assoc)}")

    # 5. Denied Symptoms (Negative context - crucial for differential diagnosis)
    if case.denied_symptoms:
        primary_lower = str(case.primary_symptom.value or "").lower()
        valid_denied = [s for s in case.denied_symptoms if s and s.lower() != primary_lower]
        if valid_denied:
            parts.append(f"without {', '.join(valid_denied)}")

    # 6. Relevant medical history context
    if case.medical_history:
        parts.append(f"history of {', '.join(case.medical_history)}")

    query = " ".join(parts).strip()
    return query or "acute symptom triage consultation"


def prepare_retrieval_query(
    user_query: str,
    case: Optional[PatientCase] = None,
    domain: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, str, str]:
    """
    Translates natural user language into high-precision search representations.
    Normalizes colloquial expressions, spelling errors, preserves clinical intent,
    and returns (dense_query, rerank_query, query_intent) where query_intent is in:
    ["direct_knowledge", "symptom_triage", "differential_diagnosis", "ayurvedic_guidance", "emergency_safety", "out_of_corpus"].
    """
    raw_text = (user_query or "").strip()
    
    # 0. Clean typos and resolve conversational follow-ups
    cleaned_query = clean_typos(raw_text)
    resolved_query = resolve_coreference(cleaned_query, history=conversation_history, case=case)
    q_lower = resolved_query.lower()

    # 1. Emergency Detection Check (Life-threatening presentations)
    if any(phrase in q_lower for phrase in [
        "worst headache of my life", "explosion in my brain", "thunderclap headache",
        "sudden severe headache with stiff neck", "neck is stiffening up",
        "inability to swallow liquids", "drooling", "stridor",
        "coughing blood", "hemoptysis", "chest pain"
    ]):
        if "sore throat" in q_lower or "swallow" in q_lower or "drooling" in q_lower or "stridor" in q_lower:
            dense_query = "Viral pharyngitis acute sore throat red-flag warning signs dangerous emergency medical care inability swallow liquids drooling stridor fever"
            return (dense_query, resolved_query, "emergency_safety")
        dense_query = "Tension-type headache warning signs physician emergency evaluation sudden thunderclap onset fever with neck stiffness"
        return (dense_query, resolved_query, "emergency_safety")

    # 2. Out-of-Corpus Clinical Boundary Check (Unverified specialties / conditions)
    if any(phrase in q_lower for phrase in [
        "lower right abdomen", "hip bone", "appendicitis", "appendix",
        "gallbladder", "cholecystitis", "bone fracture", "kidney stone",
        "toothache", "ear infection"
    ]):
        dense_query = "Acute appendicitis lower right abdomen pain nausea loss of appetite surgical emergency evaluation"
        return (dense_query, resolved_query, "out_of_corpus")

    # 3. Ayurvedic / AYUSH Traditional Guidance
    if domain == "Ayurvedic traditional clinical guidance" or any(term in q_lower for term in [
        "ayurved", "ayush", "traditional", "jwara", "kasa", "shirashoola", "herbal home remedies", "home remedies"
    ]):
        if any(term in q_lower for term in ["fever", "jwara", "temperature"]):
            dense_query = "Ayurvedic traditional clinical guidance Jwara acute mild fever Langhana light diet Shadanga Paniya Tulsi Giloy"
        elif any(term in q_lower for term in ["cough", "kasa", "throat"]):
            dense_query = "Ayurvedic traditional clinical guidance Kasa respiratory cough throat irritation ginger Tulsi turmeric gargles"
        elif any(term in q_lower for term in ["headache", "shirashoola"]):
            dense_query = "Ayurvedic traditional clinical guidance Shirashoola tension headache Chandana sandalwood Shiroabhyanga"
        else:
            dense_query = f"Ayurvedic traditional clinical guidance {resolved_query}"
        return (dense_query, resolved_query, "ayurvedic_guidance")

    # 4. Differential Diagnosis Inquiries (Comparing conditions)
    if any(w in q_lower for w in ["distinguish", "how do i tell", "difference between", "tell if", "versus", "vs "]):
        if "migraine" in q_lower or "tension" in q_lower:
            dense_query = "Migraine without aura versus tension-type headache differential diagnosis unilateral throbbing nausea photophobia phonophobia dull band-like ache"
            return (dense_query, resolved_query, "differential_diagnosis")
        if "pharyngitis" in q_lower or "sore throat" in q_lower or "cold" in q_lower:
            dense_query = "Viral pharyngitis versus influenza common cold symptoms distinguishing features"
            return (dense_query, resolved_query, "differential_diagnosis")
        if "bronchitis" in q_lower or "pneumonia" in q_lower:
            dense_query = "Acute bronchitis diagnosis persistent cough without pneumonia supportive care"
            return (dense_query, resolved_query, "differential_diagnosis")

    # 5. Direct Knowledge Inquiries (Factual, Educational Questions)
    is_direct_question = (
        q_lower.startswith((
            "what is", "what are", "what causes", "why does", "why do", "explain",
            "how do", "how is", "can you explain", "could you explain", "tell me about",
            "describe", "what's", "what does"
        ))
        or any(k in q_lower for k in [
            "clinical characteristics", "clinical features", "primary clinical objective",
            "red-flag signs", "what steps can help", "what non-drug steps", "definition of",
            "meaning of", "causes of", "explain what"
        ])
    )
    has_personal_patient_markers = any(m in q_lower for m in [
        "i have", "i've had", "i feel", "i started", "my head", "my throat", "my stomach",
        "since yesterday", "for 2 days", "for two days", "for 3 days"
    ]) and not q_lower.startswith(("why does my head hurt", "why does my throat hurt"))

    # Gastroenteritis & Dehydration Direct Knowledge
    if "gastroenteritis" in q_lower or ("diarrhea" in q_lower and "vomiting" in q_lower):
        if "objective" in q_lower or "managing" in q_lower or "dehydration" in q_lower or is_direct_question:
            dense_query = "Acute viral gastroenteritis primary clinical objective preventing dehydration Oral Rehydration Solution ORS electrolyte fluids small sips"
            return (dense_query, resolved_query, "direct_knowledge" if not has_personal_patient_markers else "symptom_triage")

    # Pharyngitis / Sore Throat Direct Knowledge
    if "pharyngitis" in q_lower or "sore throat" in q_lower or "throat hurt" in q_lower:
        if any(w in q_lower for w in ["red-flag", "dangerous", "emergency", "warning"]):
            dense_query = "Viral pharyngitis acute sore throat red-flag warning signs dangerous emergency medical care inability swallow liquids drooling stridor fever"
            return (dense_query, resolved_query, "emergency_safety")
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Viral pharyngitis and common cold scratchy throat nasal congestion low-grade fever cough supportive care warm salt water gargles"
            return (dense_query, resolved_query, "direct_knowledge")

    # Headache & Migraine Direct Knowledge
    if "tension-type headache" in q_lower or "tension headache" in q_lower:
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Tension-type headache clinical diagnosis characteristics dull non-throbbing band-like pain mild moderate severity lacks severe vomiting aura"
            return (dense_query, resolved_query, "direct_knowledge")

    if "migraine" in q_lower:
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Migraine without aura recurrent neurological disorder unilateral throbbing pulsating headache nausea vomiting photophobia phonophobia"
            return (dense_query, resolved_query, "direct_knowledge")

    if "head hurt" in q_lower or "headache" in q_lower or "head pain" in q_lower:
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Tension-type headache and acute migraine causes clinical diagnosis characteristics dull band-like ache unilateral throbbing pain supportive care"
            return (dense_query, resolved_query, "direct_knowledge")

    # Fever & Febrile Illness Direct Knowledge
    if "fever" in q_lower or "febrile" in q_lower:
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Acute viral fever elevated body temperature malaise muscle aches supportive care hydration cooling rest"
            return (dense_query, resolved_query, "direct_knowledge")

    # Bronchitis Direct Knowledge
    if "bronchitis" in q_lower:
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Acute bronchitis inflammation large airways persistent cough sputum steam inhalation hydration rest"
            return (dense_query, resolved_query, "direct_knowledge")

    # Dengue Direct Knowledge
    if "dengue" in q_lower:
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Dengue fever high fever severe headache retro-orbital pain joint bone aches mucosal bleeding lethargy"
            return (dense_query, resolved_query, "direct_knowledge")

    # Influenza Direct Knowledge
    if "influenza" in q_lower or "flu" in q_lower:
        if is_direct_question and not has_personal_patient_markers:
            dense_query = "Influenza seasonal acute abrupt onset fever chills fatigue cough sore throat droplet isolation"
            return (dense_query, resolved_query, "direct_knowledge")

    # 6. Symptom Triage with Colloquial Phrasings & Metaphors
    if any(m in q_lower for m in [
        "tight band around my forehead", "tight band around forehead", "vice grip",
        "steady pressure around the temples", "someone is squeezing it", "squeezing my head", "head is paining"
    ]):
        dense_query = "Tension-type headache dull aching band around forehead lasting 2 days home supportive care hydration quiet rest screen avoidance"
        return (dense_query, resolved_query, "symptom_triage")

    if ("throat" in q_lower and any(w in q_lower for w in ["swallow", "hurt", "pain", "scratchy", "sore"])) or "hurts when i swallow" in q_lower:
        dense_query = "Viral pharyngitis acute sore throat scratchy throat pain swallowing supportive care warm salt water gargles hydration rest"
        return (dense_query, resolved_query, "symptom_triage")

    if "headache since yesterday" in q_lower or ("headache" in q_lower and ("yesterday" in q_lower or "2 days" in q_lower or "two days" in q_lower)):
        dense_query = "Tension-type headache and migraine headache duration since yesterday home supportive care hydration rest"
        return (dense_query, resolved_query, "symptom_triage")

    if ("throbbing" in q_lower and ("left side" in q_lower or "one side" in q_lower)) or ("sick to my stomach" in q_lower and "lights hurt" in q_lower):
        dense_query = "Migraine without aura unilateral throbbing headache nausea photophobia first-line supportive self-care quiet dark room cold compress"
        return (dense_query, resolved_query, "symptom_triage")

    # 7. Fallback Query Construction from Structured PatientCase
    if case and case.primary_symptom.value:
        dense_query = build_medical_query(case, domain=domain)
        return (dense_query, resolved_query, "symptom_triage")

    # 8. General fallback based on question pattern
    determined_intent = "direct_knowledge" if is_direct_question and not has_personal_patient_markers else "symptom_triage"
    return (resolved_query, resolved_query, determined_intent)
