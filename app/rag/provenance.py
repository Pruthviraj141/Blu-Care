from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentReviewStatus(str, Enum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    SUPERSEDED = "superseded"
    QUARANTINED = "quarantined"


class MedicalDocumentMetadata(BaseModel):
    """Complete provenance contract for every medical knowledge chunk."""
    document_id: str
    chunk_id: str
    source_id: str

    title: str
    publisher: str = "WHO / Peer-Reviewed Clinical Standard"

    source_url: Optional[str] = None
    doi: Optional[str] = None

    source_type: Optional[str] = "clinical_guideline"  # clinical_guideline, textbook, research_article
    publication_date: Optional[str] = None
    updated_date: Optional[str] = None

    jurisdiction: Optional[str] = "Global"
    population: Optional[str] = "general"
    language: str = "en"

    clinical_topic: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None

    content_hash: str
    ingestion_version: str = "2.0.0"
    review_status: DocumentReviewStatus = DocumentReviewStatus.APPROVED


class ApprovedSource(BaseModel):
    source_id: str
    name: str
    publisher: str
    base_url: Optional[str] = None
    status: DocumentReviewStatus = DocumentReviewStatus.APPROVED
    description: str


APPROVED_SOURCE_REGISTRY: List[ApprovedSource] = [
    ApprovedSource(
        source_id="WHO-PCD",
        name="WHO Primary Care Triage Protocols",
        publisher="World Health Organization",
        base_url="https://www.who.int/publications",
        description="International evidence-based standards for primary care diagnosis and symptom triage.",
    ),
    ApprovedSource(
        source_id="NICE-CG",
        name="NICE Clinical Guidelines",
        publisher="National Institute for Health and Care Excellence",
        base_url="https://www.nice.org.uk/guidance",
        description="UK national evidence-based guidance for medical triage and assessment.",
    ),
    ApprovedSource(
        source_id="CDC-CLINICAL",
        name="CDC Clinical Disease Reference",
        publisher="Centers for Disease Control and Prevention",
        base_url="https://www.cdc.gov",
        description="Public health and infectious disease diagnostic criteria.",
    ),
]
