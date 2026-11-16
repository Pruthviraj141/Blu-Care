"""
Dataset schema and loader for BluCare+ Medical RAG evaluation.
Validates structure, ensures presence of mandatory fields, and validates
ground truth against ingested medical document identifiers.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Canonical document IDs present in production Qdrant collection
VALID_DOC_IDS = {
    "MED-TENSION-HEADACHE-01",
    "MED-MIGRAINE-WITHOUT-AURA-02",
    "MED-VIRAL-PHARYNGITIS-03",
    "MED-ACUTE-GASTROENTERITIS-04",
    "MED-ACUTE-BRONCHITIS-05",
    "MED-VIRAL-FEVER-06",
    "MED-DENGUE-FEVER-07",
    "MED-INFLUENZA-08",
    "AYU-FEVER-JWARA-01",
    "AYU-RESPIRATORY-KASA-02",
    "AYU-HEADACHE-SHIRASHOOLA-03",
}

CaseCategory = Literal[
    "direct_knowledge",
    "symptom_triage",
    "differential_diagnosis",
    "ayurvedic_guidance",
    "out_of_corpus",
    "insufficient_evidence",
    "emergency_safety",
]

SufficiencyStatus = Literal[
    "sufficient",
    "insufficient",
    "emergency_abstention",
]


class MedicalTestCase(BaseModel):
    case_id: str = Field(description="Unique identifier e.g. 'CASE-TH-01'")
    user_question: str = Field(description="Patient or clinical query text")
    clinical_topic: str = Field(description="Medical specialty / topic e.g. 'Neurology / Headache'")
    reference_answer: str = Field(description="Authoritative, evidence-grounded clinical answer")
    expected_facts: List[str] = Field(default_factory=list, description="Key facts required in grounded response")
    expected_document_ids: List[str] = Field(default_factory=list, description="Target document IDs expected in retrieval")
    reference_contexts: List[str] = Field(default_factory=list, description="Exact ground-truth quotes from corpus")
    expected_evidence_sufficiency: SufficiencyStatus = Field(default="sufficient")
    case_category: CaseCategory = Field(default="symptom_triage")

    @field_validator("expected_document_ids")
    @classmethod
    def validate_document_ids(cls, doc_ids: List[str]) -> List[str]:
        for doc_id in doc_ids:
            if doc_id not in VALID_DOC_IDS:
                raise ValueError(
                    f"Invalid expected_document_id '{doc_id}'. Must be one of {sorted(list(VALID_DOC_IDS))}"
                )
        return doc_ids


class MedicalEvaluationDataset(BaseModel):
    version: str = "1.0.0"
    created_at: str = "2026-11-12"
    total_cases: int
    cases: List[MedicalTestCase]


def load_evaluation_dataset(dataset_path: Path) -> List[MedicalTestCase]:
    """Loads and validates the golden evaluation dataset from JSON."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "cases" in data:
        raw_cases = data["cases"]
    elif isinstance(data, list):
        raw_cases = data
    else:
        raise ValueError("Invalid dataset structure. Expected a list of cases or an object with 'cases' key.")

    cases = [MedicalTestCase(**c) for c in raw_cases]
    logger.info("Successfully loaded and validated %d medical test cases from %s", len(cases), dataset_path)
    return cases

