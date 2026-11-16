import logging
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models import TriageSession, TriageMessage, TriageSafetyEvent, TriageAssessment

logger = logging.getLogger(__name__)


class TriageRepository:
    """Encapsulates all database operations with strict Clerk user ownership enforcement."""

    @staticmethod
    def create_session(
        db: Session,
        clerk_user_id: str,
        initial_case_state: Optional[Dict[str, Any]] = None,
        pending_question: Optional[str] = None,
        status: str = "intake",
    ) -> TriageSession:
        session = TriageSession(
            clerk_user_id=clerk_user_id,
            status=status,
            case_state=initial_case_state or {},
            pending_question=pending_question,
            version=1,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: str, clerk_user_id: str) -> Optional[TriageSession]:
        """Gets a session verifying ownership."""
        return (
            db.query(TriageSession)
            .filter(TriageSession.id == session_id, TriageSession.clerk_user_id == clerk_user_id)
            .first()
        )

    @staticmethod
    def list_user_sessions(db: Session, clerk_user_id: str, limit: int = 50) -> List[TriageSession]:
        """Lists sessions owned by user ordered by most recently updated."""
        return (
            db.query(TriageSession)
            .filter(TriageSession.clerk_user_id == clerk_user_id)
            .order_by(desc(TriageSession.updated_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_session_state(
        db: Session,
        session_id: str,
        clerk_user_id: str,
        case_state: Dict[str, Any],
        pending_question: Optional[str],
        status: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> TriageSession:
        """Updates case state and pending question with optimistic concurrency protection."""
        query = db.query(TriageSession).filter(
            TriageSession.id == session_id,
            TriageSession.clerk_user_id == clerk_user_id,
        )
        if expected_version is not None:
            query = query.filter(TriageSession.version == expected_version)

        session = query.first()
        if not session:
            raise ValueError(f"Session {session_id} not found or version conflict.")

        session.case_state = case_state
        session.pending_question = pending_question
        if status:
            session.status = status
        session.version += 1
        session.updated_at = datetime.datetime.now(datetime.timezone.utc)

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(db: Session, session_id: str, clerk_user_id: str) -> bool:
        """Deletes session and all cascading records (messages, safety events)."""
        session = (
            db.query(TriageSession)
            .filter(TriageSession.id == session_id, TriageSession.clerk_user_id == clerk_user_id)
            .first()
        )
        if not session:
            return False

        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def add_message(
        db: Session,
        session_id: str,
        role: str,
        content: str,
        turn_id: int = 1,
        idempotency_key: Optional[str] = None,
    ) -> TriageMessage:
        """Appends a message to the session."""
        if idempotency_key:
            existing = (
                db.query(TriageMessage)
                .filter(TriageMessage.session_id == session_id, TriageMessage.idempotency_key == idempotency_key)
                .first()
            )
            if existing:
                return existing

        message = TriageMessage(
            session_id=session_id,
            role=role,
            content=content,
            turn_id=turn_id,
            idempotency_key=idempotency_key,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_messages(db: Session, session_id: str) -> List[TriageMessage]:
        """Gets all messages for a session ordered by creation time."""
        return (
            db.query(TriageMessage)
            .filter(TriageMessage.session_id == session_id)
            .order_by(TriageMessage.created_at.asc())
            .all()
        )

    @staticmethod
    def record_safety_event(
        db: Session,
        session_id: str,
        rule_id: str,
        ruleset_version: str,
        outcome: str,
        message_id: Optional[str] = None,
    ) -> TriageSafetyEvent:
        """Records an emergency safety event."""
        event = TriageSafetyEvent(
            session_id=session_id,
            message_id=message_id,
            rule_id=rule_id,
            ruleset_version=ruleset_version,
            outcome=outcome,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def save_assessment(
        db: Session,
        session_id: str,
        user_id: str,
        assessment_json: Dict[str, Any],
        evidence_source_ids: List[str],
        assessment_version: str = "1.0.0",
        safety_ruleset_version: str = "1.0.0",
        rag_configuration_version: str = "1.0.0",
    ) -> TriageAssessment:
        """
        Persists a structured clinical assessment for a session.
        Idempotent: updates existing assessment if already present for this session,
        or creates a new record.
        """
        existing = (
            db.query(TriageAssessment)
            .filter(
                TriageAssessment.session_id == session_id,
                TriageAssessment.user_id == user_id,
            )
            .order_by(TriageAssessment.created_at.desc())
            .first()
        )
        if existing:
            existing.assessment_json = assessment_json
            existing.evidence_source_ids = evidence_source_ids
            existing.assessment_version = assessment_version
            existing.safety_ruleset_version = safety_ruleset_version
            existing.rag_configuration_version = rag_configuration_version
            db.commit()
            db.refresh(existing)
            return existing

        assessment = TriageAssessment(
            session_id=session_id,
            user_id=user_id,
            assessment_version=assessment_version,
            assessment_json=assessment_json,
            evidence_source_ids=evidence_source_ids,
            safety_ruleset_version=safety_ruleset_version,
            rag_configuration_version=rag_configuration_version,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def get_assessment_by_id(
        db: Session,
        assessment_id: str,
        user_id: str,
    ) -> Optional[TriageAssessment]:
        """Fetches assessment by ID with user ownership check."""
        return (
            db.query(TriageAssessment)
            .filter(
                TriageAssessment.id == assessment_id,
                TriageAssessment.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def get_assessment_by_session_id(
        db: Session,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[TriageAssessment]:
        """Fetches assessment for session with optional user ownership check."""
        query = db.query(TriageAssessment).filter(TriageAssessment.session_id == session_id)
        if user_id:
            query = query.filter(TriageAssessment.user_id == user_id)
        return query.order_by(TriageAssessment.created_at.desc()).first()

    @staticmethod
    def get_latest_assessment(
        db: Session,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[TriageAssessment]:
        """Convenience method to fetch the most recent assessment for a session."""
        return TriageRepository.get_assessment_by_session_id(db, session_id, user_id)

