"""
Disease-Aware Facility and Medical Specialty Mapper for BluCare+.

Maps clinical conditions, symptom findings, and urgency tiers to targeted
search terms and verification criteria. Ensures that facility discoveries reflect
the patient's true medical needs while maintaining strict geographical distance ranking.
"""

import re
from typing import Dict, Any, List, Optional, Set

SPECIALTY_PROFILES: List[Dict[str, Any]] = [
    {
        "condition_id": "cardiac",
        "keywords": [
            "cardiac", "heart", "chest pain", "angina", "myocardial", "infarction",
            "palpitation", "arrhythmia", "coronary", "shortness of breath", "ecg"
        ],
        "specialty_name": "Cardiology / Emergency Cardiac Care",
        "search_query": "cardiac hospital heart institute cardiology emergency",
        "preferred_category": "hospital",
        "emergency_required": True,
        "verified_types": {
            "heart hospital", "cardiology", "cardiologist", "hospital",
            "general hospital", "multispecialty hospital", "emergency room", "medical center"
        },
    },
    {
        "condition_id": "orthopedic",
        "keywords": [
            "fracture", "trauma", "accident", "bone", "orthopedic", "sprain",
            "dislocation", "fall injury", "joint pain", "knee", "hip", "spine"
        ],
        "specialty_name": "Orthopedics & Emergency Trauma",
        "search_query": "orthopedic hospital bone joint clinic trauma center",
        "preferred_category": "hospital",
        "emergency_required": False,
        "verified_types": {
            "orthopedic clinic", "orthopedic surgeon", "hospital",
            "general hospital", "multispecialty hospital", "trauma center", "medical center"
        },
    },
    {
        "condition_id": "emergency",
        "keywords": [
            "emergency", "unconscious", "collapse", "severe bleeding", "critical",
            "acute", "casualty", "ambulance", "trauma", "anaphylaxis", "poisoning"
        ],
        "specialty_name": "24/7 Emergency & Critical Care",
        "search_query": "emergency hospital 24 hour casualty trauma center",
        "preferred_category": "hospital",
        "emergency_required": True,
        "verified_types": {
            "hospital", "general hospital", "multispecialty hospital",
            "emergency room", "trauma center", "medical center"
        },
    },
    {
        "condition_id": "pediatric",
        "keywords": [
            "pediatric", "child", "children", "infant", "baby", "toddler",
            "neonatal", "pediatrics", "pediatrician"
        ],
        "specialty_name": "Pediatrics / Child Healthcare",
        "search_query": "children hospital pediatric clinic pediatrician",
        "preferred_category": "clinic",
        "emergency_required": False,
        "verified_types": {
            "children's hospital", "pediatrician", "pediatric clinic",
            "hospital", "general hospital", "clinic", "medical center"
        },
    },
    {
        "condition_id": "dental",
        "keywords": ["dental", "tooth", "teeth", "gum", "dentist", "toothache", "cavity"],
        "specialty_name": "Dental Care",
        "search_query": "dental clinic dentist hospital",
        "preferred_category": "clinic",
        "emergency_required": False,
        "verified_types": {"dental clinic", "dentist", "dental hospital"},
    },
    {
        "condition_id": "ophthalmology",
        "keywords": [
            "eye", "vision", "ophthalmology", "cataract", "cornea",
            "glaucoma", "blindness", "optometry", "eye injury"
        ],
        "specialty_name": "Ophthalmology / Eye Care",
        "search_query": "eye hospital ophthalmology clinic eye care",
        "preferred_category": "clinic",
        "emergency_required": False,
        "verified_types": {"eye hospital", "ophthalmologist", "eye care center", "hospital"},
    },
    {
        "condition_id": "dermatology",
        "keywords": ["skin", "rash", "dermatology", "eczema", "psoriasis", "itching", "lesion", "dermatitis"],
        "specialty_name": "Dermatology",
        "search_query": "dermatologist skin clinic dermatology center",
        "preferred_category": "clinic",
        "emergency_required": False,
        "verified_types": {"dermatologist", "skin clinic", "clinic", "hospital"},
    },
    {
        "condition_id": "maternity",
        "keywords": [
            "pregnancy", "maternity", "obstetric", "gynecology", "prenatal",
            "labor pain", "delivery", "gynecologist"
        ],
        "specialty_name": "Maternity & Obstetrics",
        "search_query": "maternity hospital women hospital gynecology center",
        "preferred_category": "hospital",
        "emergency_required": True,
        "verified_types": {
            "maternity hospital", "women's health clinic", "gynecologist",
            "hospital", "general hospital", "multispecialty hospital"
        },
    },
    {
        "condition_id": "fever",
        "keywords": [
            "fever", "cough", "cold", "flu", "weakness", "infection",
            "headache", "fatigue", "viral", "malaise", "body ache", "general"
        ],
        "specialty_name": "General Medicine & Outpatient Care",
        "search_query": "general hospital physician outpatient clinic",
        "preferred_category": "all",
        "emergency_required": False,
        "verified_types": {
            "general hospital", "hospital", "clinic", "medical clinic",
            "general practitioner", "doctor", "health center", "dispensary"
        },
    },
]


def map_condition_to_facility_query(
    condition_name: Optional[str] = None,
    symptoms: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Analyzes condition title and symptoms to recommend disease-targeted facility search.
    Returns:
    {
        "condition_id": str,
        "specialty_name": str,
        "search_query": str,
        "primary_queries": List[str],  # For backwards compatibility
        "preferred_category": str,
        "emergency_required": bool,
        "emergency_priority": bool,     # For backwards compatibility
        "verified_types": Set[str],
        "matched_keywords": List[str],
    }
    """
    text_corpus = []
    if condition_name:
        text_corpus.append(str(condition_name).lower())
    if symptoms:
        for s in symptoms:
            if isinstance(s, str):
                text_corpus.append(s.lower())
            elif isinstance(s, dict) and "name" in s:
                text_corpus.append(str(s["name"]).lower())

    combined_text = " ".join(text_corpus)

    for profile in SPECIALTY_PROFILES:
        matched = []
        for kw in profile["keywords"]:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, combined_text, re.IGNORECASE):
                matched.append(kw)

        if matched:
            return {
                "condition_id": profile["condition_id"],
                "specialty_name": profile["specialty_name"],
                "search_query": profile["search_query"],
                "primary_queries": [profile["search_query"], "hospital", "clinic"],
                "preferred_category": profile["preferred_category"],
                "emergency_required": profile["emergency_required"],
                "emergency_priority": profile["emergency_required"],
                "verified_types": profile["verified_types"],
                "matched_keywords": matched,
            }

    # Default fallback: General healthcare
    return {
        "condition_id": "general",
        "specialty_name": "General Healthcare / Outpatient Clinic",
        "search_query": "hospitals clinics general physician",
        "primary_queries": ["hospital", "clinic"],
        "preferred_category": "all",
        "emergency_required": False,
        "emergency_priority": False,
        "verified_types": {
            "hospital", "general hospital", "clinic", "medical clinic",
            "general practitioner", "doctor", "health center"
        },
        "matched_keywords": [],
    }


def verify_facility_specialty(
    facility_type: str,
    facility_name: str,
    specialty_info: Dict[str, Any],
    is_emergency: str = "no",
) -> Dict[str, Any]:
    """
    Verifies if a scraped facility is clinically relevant to the patient's condition.
    Does NOT accept an unrelated clinic simply because the name matches a keyword.
    
    Returns:
    {
        "is_relevant": bool,
        "verified_specialty": str,
        "relevance_reason": str,
    }
    """
    norm_type = (facility_type or "").lower().strip()
    norm_name = (facility_name or "").lower().strip()
    allowed_types = specialty_info.get("verified_types", set())
    condition_id = specialty_info.get("condition_id", "general")

    # Rule 1: Direct match in classified facility type
    for t in allowed_types:
        if t in norm_type or norm_type in t:
            return {
                "is_relevant": True,
                "verified_specialty": specialty_info.get("specialty_name", "General Healthcare"),
                "relevance_reason": f"Facility classified as '{facility_type}' matching {specialty_info.get('specialty_name')}",
            }

    # Rule 2: Major General / Multispecialty hospitals with 24/7 casualty handle emergencies
    if any(h in norm_type for h in ["hospital", "medical center"]) or any(h in norm_name for h in ["hospital", "medical center"]):
        if is_emergency == "yes" or specialty_info.get("emergency_required", False):
            return {
                "is_relevant": True,
                "verified_specialty": f"Full-Service Hospital ({specialty_info.get('specialty_name')})",
                "relevance_reason": "Full-service hospital capable of emergency triage and specialized inpatient admissions",
            }
        return {
            "is_relevant": True,
            "verified_specialty": specialty_info.get("specialty_name", "General Healthcare"),
            "relevance_reason": "General hospital equipped with multidisciplinary medical staff",
        }

    # Rule 3: For general / fever inquiries, any medical clinic or general practice is valid
    if condition_id in ("general", "fever") and any(c in norm_type for c in ["clinic", "doctor", "health"]):
        return {
            "is_relevant": True,
            "verified_specialty": "Outpatient General Medicine",
            "relevance_reason": "Primary care clinic suitable for outpatient evaluation",
        }

    # Rule 4: Reject unrelated specialized clinics (e.g. dental clinic for chest pain)
    return {
        "is_relevant": False,
        "verified_specialty": facility_type or "Unverified",
        "relevance_reason": f"Facility type '{facility_type}' does not provide services for {specialty_info.get('specialty_name')}",
    }
