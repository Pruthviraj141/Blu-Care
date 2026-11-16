import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.db.session import SessionLocal
from app.db.repository import TriageRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Clinical Assessments"])


class AssessmentDetailResponse(BaseModel):
    assessment_id: str
    session_id: str
    user_id: str
    assessment_version: str
    assessment: Dict[str, Any]
    evidence_source_ids: List[str]
    safety_ruleset_version: str
    rag_configuration_version: str
    created_at: str


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment_by_id(
    assessment_id: str,
    user_id: str = Depends(get_current_user),
):
    """Retrieves a persisted clinical triage assessment by assessment ID with strict user ownership."""
    db = SessionLocal()
    try:
        record = TriageRepository.get_assessment_by_id(db, assessment_id, user_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found or access denied.",
            )
        return AssessmentDetailResponse(
            assessment_id=record.id,
            session_id=record.session_id,
            user_id=record.user_id,
            assessment_version=record.assessment_version,
            assessment=record.assessment_json,
            evidence_source_ids=record.evidence_source_ids or [],
            safety_ruleset_version=record.safety_ruleset_version,
            rag_configuration_version=record.rag_configuration_version,
            created_at=record.created_at.isoformat(),
        )
    finally:
        db.close()


@router.get("/session/{session_id}/assessment", response_model=AssessmentDetailResponse)
@router.get("/sessions/{session_id}/assessment", response_model=AssessmentDetailResponse)
async def get_session_assessment(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """Retrieves the latest persisted clinical triage assessment for a session thread with strict user ownership."""
    db = SessionLocal()
    try:
        record = TriageRepository.get_assessment_by_session_id(db, session_id, user_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No clinical assessment recorded for this session yet or access denied.",
            )
        return AssessmentDetailResponse(
            assessment_id=record.id,
            session_id=record.session_id,
            user_id=record.user_id,
            assessment_version=record.assessment_version,
            assessment=record.assessment_json,
            evidence_source_ids=record.evidence_source_ids or [],
            safety_ruleset_version=record.safety_ruleset_version,
            rag_configuration_version=record.rag_configuration_version,
            created_at=record.created_at.isoformat(),
        )
    finally:
        db.close()
