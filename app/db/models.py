import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class TriageSession(Base):
    """Authoritative persistent record of a patient triage session and structured state."""
    __tablename__ = "triage_sessions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    clerk_user_id = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="intake")  # intake, assessment_ready, emergency, completed
    case_state = Column(JSON, nullable=False, default=dict)
    pending_question = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    messages = relationship("TriageMessage", back_populates="session", cascade="all, delete-orphan", order_by="TriageMessage.created_at")
    safety_events = relationship("TriageSafetyEvent", back_populates="session", cascade="all, delete-orphan")
    assessments = relationship("TriageAssessment", back_populates="session", cascade="all, delete-orphan", order_by="TriageAssessment.created_at.desc()")

    __table_args__ = (
        Index("ix_triage_sessions_user_status", "clerk_user_id", "status"),
    )


class TriageMessage(Base):
    """Authoritative persistent record of a single conversation turn."""
    __tablename__ = "triage_messages"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), ForeignKey("triage_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    turn_id = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("TriageSession", back_populates="messages")


class TriageSafetyEvent(Base):
    """Audit log for matched safety rules and emergency escalations."""
    __tablename__ = "triage_safety_events"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), ForeignKey("triage_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(64), nullable=True)
    rule_id = Column(String(64), nullable=False)
    ruleset_version = Column(String(32), nullable=False)
    outcome = Column(String(32), nullable=False)  # emergency_detected, safety_review_required
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("TriageSession", back_populates="safety_events")


class TriageAssessment(Base):
    """Authoritative persistent record of a structured clinical triage assessment."""
    __tablename__ = "triage_assessments"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), ForeignKey("triage_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    assessment_version = Column(String(32), nullable=False, default="1.0.0")
    assessment_json = Column(JSON, nullable=False)
    evidence_source_ids = Column(JSON, nullable=False, default=list)
    safety_ruleset_version = Column(String(32), nullable=False, default="1.0.0")
    rag_configuration_version = Column(String(32), nullable=False, default="1.0.0")
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("TriageSession", back_populates="assessments")

    __table_args__ = (
        Index("ix_triage_assessments_user_session", "user_id", "session_id"),
    )

