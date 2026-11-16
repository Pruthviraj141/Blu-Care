import asyncio
import logging
import time
import uuid
from typing import Tuple, Dict, Any, List, AsyncGenerator, Optional
import anyio
from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, AIMessage

import json
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import TriageSession
from app.db.repository import TriageRepository
from app.schemas.api import SessionItem, HistoricalMessage
from app.services.patient_case import PatientCase, FactStatus
from app.services.safety_engine import SafetyEngine
from app.services.symptom_extractor import SymptomExtractor
from app.services.question_planner import QuestionPlanner
from app.services.patient_lookup import PatientLookupEngine
from app.graph.build_graph import compiled_graph

logger = logging.getLogger(__name__)


class SessionService:
    """Authoritative, database-backed triage session coordinator."""

    @staticmethod
    def start_session(initial_message: str = None, user_id: str = "anonymous_patient") -> Tuple[str, str]:
        """Creates a persistent session in the database and evaluates initial symptom message."""
        db = SessionLocal()
        try:
            case = PatientCase()

            # 1. Deterministic Greeting Check (Zero LLM Tokens)
            greeting_reply = PatientLookupEngine.check_greeting(initial_message or "", case)
            if greeting_reply:
                initial_reply = greeting_reply
                case.record_question_asked(
                    category="primary_symptom",
                    question_text=greeting_reply,
                    field="primary_symptom",
                    turn_id=1,
                )
            elif initial_message and initial_message.strip():
                # 2. Emergency Safety Engine Check
                safety_result = SafetyEngine.evaluate(initial_message)
                if safety_result.is_emergency:
                    case.intake_status = "emergency"
                    session = TriageRepository.create_session(
                        db=db,
                        clerk_user_id=user_id,
                        initial_case_state=case.model_dump(),
                        pending_question=None,
                        status="emergency",
                    )
                    TriageRepository.add_message(db, session.id, "user", initial_message, turn_id=1)
                    bot_msg = TriageRepository.add_message(db, session.id, "assistant", safety_result.emergency_message, turn_id=1)
                    TriageRepository.record_safety_event(
                        db=db,
                        session_id=session.id,
                        rule_id=safety_result.rule_id or "EMERGENCY",
                        ruleset_version=safety_result.ruleset_version,
                        outcome=safety_result.outcome,
                        message_id=bot_msg.id,
                    )
                    return session.id, safety_result.emergency_message

                # Direct Knowledge & Educational Question Fast-Path Routing
                from app.rag.query_builder import prepare_retrieval_query
                _, _, query_intent = prepare_retrieval_query(initial_message, case=case)
                if query_intent in ("direct_knowledge", "ayurvedic_guidance"):
                    session = TriageRepository.create_session(
                        db=db,
                        clerk_user_id=user_id,
                        initial_case_state=case.model_dump(),
                        pending_question=None,
                    )
                    db.close()
                    res = SessionService.process_message(
                        thread_id=session.id,
                        message=initial_message,
                        user_id=user_id,
                    )
                    return session.id, res.get("message") or res.get("bot_reply", "")

                # Semantic Cache check for initial educational inquiry
                if settings.redis_cache_enabled:
                    from app.services.semantic_cache import SemanticCacheService
                    is_eligible, _ = SemanticCacheService.is_cache_eligible(initial_message, case=case, turn_id=1)
                    if is_eligible:
                        hit = SemanticCacheService.lookup(initial_message)
                        if hit:
                            session = TriageRepository.create_session(
                                db=db,
                                clerk_user_id=user_id,
                                initial_case_state=case.model_dump(),
                                pending_question=None,
                            )
                            TriageRepository.add_message(db, session.id, "user", initial_message, turn_id=1)
                            TriageRepository.add_message(db, session.id, "assistant", hit["response"], turn_id=1)
                            return session.id, hit["response"]

                # 3. Deterministic Symptom & Modifier Extraction
                symptoms_merged = PatientLookupEngine.inspect_and_merge_new_symptoms(initial_message, case, turn_id=1)

                # 4. Supplementary Extraction for Complex Phrases (Only if deterministic lookup didn't resolve)
                if not symptoms_merged:
                    extracted = SymptomExtractor.extract(initial_message)
                    if extracted.symptoms:
                        for sym_item in extracted.symptoms:
                            case.add_or_update_symptom(
                                name=sym_item.name,
                                status=sym_item.status,
                                duration=sym_item.duration or extracted.duration,
                                severity=sym_item.severity or extracted.severity,
                                original_wording=sym_item.original_wording,
                                turn_id=1,
                            )
                    elif extracted.primary_symptom:
                        case.add_or_update_symptom(
                            name=extracted.primary_symptom,
                            status="present",
                            duration=extracted.duration,
                            severity=extracted.severity,
                            original_wording=extracted.original_wording,
                            turn_id=1,
                        )
                    for sym in extracted.associated_symptoms:
                        case.add_or_update_symptom(name=sym, status="present", turn_id=1)
                    for den in extracted.denied_symptoms:
                        case.add_or_update_symptom(name=den, status="absent", turn_id=1)

                # 5. Adaptive Question Selection via Context Lookup
                is_complete, next_question = PatientLookupEngine.select_next_adaptive_question(case, turn_id=1)
                if is_complete:
                    case.intake_status = "assessment_ready"
                    initial_reply = "Thank you. I have enough information to prepare your clinical assessment. Let me analyze differential conditions."
                else:
                    initial_reply = next_question
            else:
                initial_reply = "Hello! What is the main symptom or discomfort you are experiencing?"
                case.record_question_asked(category="primary_symptom", question_text=initial_reply, field="primary_symptom", turn_id=1)

            session = TriageRepository.create_session(
                db=db,
                clerk_user_id=user_id,
                initial_case_state=case.model_dump(),
                pending_question=case.pending_question,
            )

            if initial_message and initial_message.strip():
                TriageRepository.add_message(db, session.id, "user", initial_message, turn_id=1)
                TriageRepository.add_message(db, session.id, "assistant", initial_reply, turn_id=1)

            return session.id, initial_reply
        finally:
            db.close()

    @staticmethod
    async def start_session_async(initial_message: str = None, user_id: str = "anonymous_patient") -> Tuple[str, str]:
        return await anyio.to_thread.run_sync(SessionService.start_session, initial_message, user_id)

    @staticmethod
    def process_message(
        thread_id: str,
        message: str,
        user_id: str = "anonymous_patient",
        action_id: Optional[str] = None,
        condition_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Processes an incoming message turn or action through the unified LangGraph triage workflow."""
        db = SessionLocal()
        try:
            session = db.query(TriageSession).filter(TriageSession.id == thread_id).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Triage session '{thread_id}' not found.",
                )
            if session.clerk_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: triage session '{thread_id}' belongs to another user.",
                )
            session_case_state = session.case_state
            turn_id = len(session.messages) + 1
        finally:
            db.close()

        from app.graph.build_graph import compiled_triage_graph
        from app.core.langfuse_client import build_langchain_trace_config

        # 1. Semantic Cache check for standalone educational medical inquiries
        cache_hit_entry = None
        is_cache_eligible = False
        bypass_reason = "cache_disabled"

        if settings.redis_cache_enabled and not action_id:
            from app.services.semantic_cache import SemanticCacheService
            db_case = None
            if session_case_state:
                try:
                    db_case = PatientCase(**session_case_state)
                except Exception:
                    db_case = None

            is_cache_eligible, bypass_reason = SemanticCacheService.is_cache_eligible(
                message, case=db_case, turn_id=turn_id
            )

            if is_cache_eligible:
                cache_hit_entry = SemanticCacheService.lookup(message)

        if cache_hit_entry:
            # Fast-path cache hit: return cached educational response immediately
            db = SessionLocal()
            try:
                TriageRepository.add_message(db, thread_id, "user", message, turn_id=turn_id)
                TriageRepository.add_message(db, thread_id, "assistant", cache_hit_entry["response"], turn_id=turn_id)
            finally:
                db.close()

            # Record cache activity in Langfuse
            try:
                from app.core.langfuse_client import get_langfuse_client
                client = get_langfuse_client()
                if client:
                    client.update_current_span(
                        metadata={
                            "cache_hit": True,
                            "cache_distance": cache_hit_entry.get("distance"),
                            "llm_calls_avoided": 1,
                            "tokens_avoided": 1700,
                            "lookup_duration_s": cache_hit_entry.get("lookup_duration_s", 0.0),
                        }
                    )
            except Exception as tr_err:
                logger.debug("Notice recording cache hit in trace: %s", tr_err)

            return {
                "message": cache_hit_entry["response"],
                "is_complete": True,
                "stage": "educational_cache",
                "symptom_facts": {},
                "risk_level": "informational",
                "confidence": 0.95,
                "sources": cache_hit_entry.get("sources", []),
                "assessment_id": None,
                "assessment": None,
                "actions": [],
                "facilities": None,
                "external_search": None,
                "ayurvedic_guidance": None,
                "cache_status": "hit",
                "cache_distance": cache_hit_entry.get("distance"),
            }

        config = build_langchain_trace_config(
            thread_id=thread_id,
            user_id=user_id,
            trace_name="blucare-triage-request",
            extra_metadata={
                "action_id": action_id,
                "has_action": bool(action_id),
                "cache_eligible": is_cache_eligible,
                "cache_bypass_reason": bypass_reason if not is_cache_eligible else None,
                "cache_hit": False,
            },
        )
        workflow_input = {
            "thread_id": thread_id,
            "user_id": user_id,
            "message": message,
            "action_id": action_id,
            "condition_id": condition_id,
            "latitude": latitude,
            "longitude": longitude,
        }

        final_state = compiled_triage_graph.invoke(workflow_input, config=config)

        # If eligible and RAG produced an answer with sources, store in Semantic Cache
        if is_cache_eligible and final_state.get("bot_reply") and final_state.get("sources"):
            try:
                from app.services.semantic_cache import SemanticCacheService
                SemanticCacheService.store(
                    query=message,
                    response=final_state["bot_reply"],
                    sources=final_state["sources"],
                )
            except Exception as store_err:
                logger.debug("Failed saving result to semantic cache: %s", store_err)

        result = {
            "message": final_state.get("bot_reply", ""),
            "is_complete": final_state.get("is_complete", False),
            "stage": final_state.get("stage", "intake"),
            "symptom_facts": final_state.get("symptom_facts", {}),
            "risk_level": final_state.get("risk_level", "not_assessed"),
            "confidence": final_state.get("confidence", 0.90),
            "sources": final_state.get("sources", []),
            "assessment_id": final_state.get("persisted_assessment_id"),
            "assessment": final_state.get("assessment"),
            "actions": final_state.get("actions", []),
            "facilities": final_state.get("facilities"),
            "external_search": final_state.get("external_search"),
            "ayurvedic_guidance": final_state.get("ayurvedic_guidance"),
        }

        logger.info(
            f"[BluCare LangGraph Trace]\n"
            f"  Thread ID: {thread_id}\n"
            f"  User Message: '{message}'\n"
            f"  Action ID: {action_id}\n"
            f"  Stage: {result['stage']}\n"
            f"  Risk Level: {result['risk_level']}\n"
            f"  Bot Reply: '{result['message'][:80]}...'\n"
            f"  Actions: {json.dumps(result['actions']) if result['actions'] else '[]'}"
        )

        return result

    @staticmethod
    async def process_message_async(
        thread_id: str,
        message: str,
        user_id: str = "anonymous_patient",
        action_id: Optional[str] = None,
        condition_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        return await anyio.to_thread.run_sync(
            SessionService.process_message,
            thread_id,
            message,
            user_id,
            action_id,
            condition_id,
            latitude,
            longitude,
        )

    @staticmethod
    async def stream_message_generator(thread_id: str, message: str, user_id: str = "anonymous_patient") -> AsyncGenerator[str, None]:
        full_result = await SessionService.process_message_async(thread_id, message, user_id)
        full_text = full_result.get("message", "")
        # Emit complete message chunk followed by standard completion token
        yield f"data: {full_text}\n\n"
        yield "data: [DONE]\n\n"

    @staticmethod
    def list_user_sessions(user_id: str) -> List[SessionItem]:
        """Returns sessions owned by user from PostgreSQL/database with real message counts."""
        db = SessionLocal()
        try:
            records = TriageRepository.list_user_sessions(db, user_id)
            user_sessions = []
            for s in records:
                first_msg = s.messages[0].content if s.messages else "Health Consultation"
                title = (first_msg[:30] + "...") if len(first_msg) > 30 else first_msg
                user_sessions.append(
                    SessionItem(
                        id=f"sess_{s.id[:8]}",
                        thread_id=s.id,
                        title=title,
                        created_at=s.created_at.timestamp(),
                        updated_at=s.updated_at.timestamp(),
                        message_count=len(s.messages),
                    )
                )
            return user_sessions
        finally:
            db.close()

    @staticmethod
    def get_session_history(thread_id: str, user_id: str) -> Dict[str, Any]:
        """Loads historical messages and patient facts from database verifying ownership."""
        db = SessionLocal()
        try:
            session = db.query(TriageSession).filter(TriageSession.id == thread_id).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Triage session '{thread_id}' not found.",
                )
            if session.clerk_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: triage session '{thread_id}' belongs to another user.",
                )

            latest_assessment = TriageRepository.get_latest_assessment(db, thread_id)
            latest_assessment_json = latest_assessment.assessment_json if latest_assessment else None

            history_msgs = []
            msg_count = len(session.messages)
            for idx, m in enumerate(session.messages):
                is_last_bot = (m.role == "assistant" and idx == msg_count - 1 and latest_assessment_json)
                msg_assessment = latest_assessment_json if is_last_bot else None
                history_msgs.append(
                    HistoricalMessage(
                        id=m.id,
                        role="user" if m.role == "user" else "bot",
                        text=m.content,
                        timestamp=m.created_at.strftime("%I:%M %p"),
                        stage=session.status,
                        is_complete=session.status in ("completed", "emergency"),
                        symptom_facts=session.case_state.get("primary_symptom", {}) if isinstance(session.case_state, dict) else {},
                        assessment=msg_assessment,
                    )
                )

            return {
                "thread_id": thread_id,
                "messages": history_msgs,
                "symptom_facts": session.case_state,
                "stage": session.status,
                "status": session.status,
                "assessment": latest_assessment_json,
            }
        finally:
            db.close()

    @staticmethod
    def delete_session(thread_id: str, user_id: str) -> bool:
        """Deletes session and all associated messages/records from the database."""
        db = SessionLocal()
        try:
            session = db.query(TriageSession).filter(TriageSession.id == thread_id).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Triage session '{thread_id}' not found.",
                )
            if session.clerk_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: triage session '{thread_id}' belongs to another user.",
                )
            TriageRepository.delete_session(db, thread_id, user_id)
            return True
        finally:
            db.close()
