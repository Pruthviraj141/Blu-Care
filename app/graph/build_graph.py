import logging
import json
import time
from typing import Optional, List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END

from fastapi import HTTPException
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.repository import TriageRepository
from app.services.patient_case import PatientCase
from app.services.safety_engine import SafetyEngine
from app.services.patient_lookup import PatientLookupEngine
from app.services.symptom_extractor import SymptomExtractor
from app.rag.query_builder import build_medical_query, prepare_retrieval_query
from app.rag.retrieval_service import MedicalRetrievalService
from app.rag.context_builder import assemble_medical_context, AssembledEvidenceContext
from app.rag.synthesizer import EvidenceGroundedSynthesizer, AyurvedicSynthesizer
from app.rag.citation_validator import CitationValidator
from app.facilities.service import FacilitiesService
from app.facilities.distance import format_distance
from app.facilities.maps_urls import build_google_maps_search_url, build_google_maps_directions_url

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    thread_id: str
    user_id: str
    message: str
    turn_id: int
    action_id: Optional[str]
    condition_id: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

    route: str
    recent_messages: list
    query_intent: Optional[str]

    case_dict: dict
    pending_before: Optional[str]
    state_before: dict

    is_emergency: bool
    emergency_data: Optional[dict]

    greeting_reply: Optional[str]
    repeat_ack: Optional[str]
    intake_complete: bool
    next_question: Optional[str]

    medical_query: Optional[str]
    retrieved_documents: list
    evidence_context: Optional[dict]
    assessment_result: Optional[dict]
    validated_citations: list
    persisted_assessment_id: Optional[str]

    bot_reply: str
    stage: str
    risk_level: str
    confidence: float
    sources: list
    assessment: Optional[dict]
    actions: list
    symptom_facts: dict
    is_complete: bool

    safety_metrics: Optional[dict]
    extraction_metrics: Optional[dict]
    question_planning_metrics: Optional[dict]
    retrieval_metrics: Optional[dict]
    rerank_metrics: Optional[dict]
    citation_metrics: Optional[dict]


# ---------------------------------------------------------------------
# 1. ENTRY ROUTER NODE
# ---------------------------------------------------------------------
def entry_router_node(state: WorkflowState) -> dict:
    action_id = state.get("action_id")
    if action_id == "GET_AYURVEDIC_GUIDANCE":
        return {"route": "ayurvedic"}
    elif action_id == "FIND_NEARBY_CLINICS":
        return {"route": "clinics"}

    # Direct conversational routing for hospital / clinic discovery
    msg = (state.get("message") or "").strip().lower()
    facility_triggers = [
        "nearby hospital", "nearby clinic", "find hospital", "find clinic",
        "nearest hospital", "nearest clinic", "hospitals near me", "clinics near me",
        "find nearby hospital", "find nearby clinics", "find healthcare",
    ]
    if any(trigger in msg for trigger in facility_triggers):
        return {"route": "clinics"}

    return {"route": "load_context"}


def route_from_entry(state: WorkflowState) -> str:
    return state.get("route", "load_context")


# ---------------------------------------------------------------------
# 2. LOAD PATIENT CONTEXT NODE
# ---------------------------------------------------------------------
def load_patient_context_node(state: WorkflowState) -> dict:
    db = SessionLocal()
    try:
        session = TriageRepository.get_session(db, state["thread_id"], clerk_user_id=state["user_id"])
        recent_messages = []
        if not session:
            # Fallback initialization
            case = PatientCase()
            pending_before = None
            turn_id = 1
        else:
            case = PatientCase(**session.case_state)
            pending_before = session.pending_question
            case.turn_count += 1
            turn_id = case.turn_count
            msgs = TriageRepository.get_messages(db, session.id)
            recent_messages = [{"role": m.role, "content": m.content} for m in msgs]

        state_before = case.to_summary_dict()
        return {
            "case_dict": case.model_dump(),
            "pending_before": pending_before,
            "state_before": state_before,
            "turn_id": turn_id,
            "recent_messages": recent_messages,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------
# 3. SAFETY ASSESSMENT NODE
# ---------------------------------------------------------------------
def safety_assessment_node(state: WorkflowState) -> dict:
    case = PatientCase(**state["case_dict"])
    message = state.get("message", "")
    t0 = time.time()
    evaluation = SafetyEngine.evaluate(
        user_message=message,
        primary_symptom=case.primary_symptom.value,
        associated_symptoms=case.associated_symptoms,
    )
    duration_s = round(time.time() - t0, 4)
    safety_metrics = {
        "duration_s": duration_s,
        "is_emergency": evaluation.is_emergency,
        "rule_id": evaluation.rule_id,
        "outcome": evaluation.outcome,
        "ruleset_version": evaluation.ruleset_version,
    }

    if evaluation.is_emergency:
        return {
            "is_emergency": True,
            "route": "emergency",
            "emergency_data": {
                "risk_level": "emergency",
                "emergency_message": evaluation.emergency_message,
                "rule_id": evaluation.rule_id,
                "outcome": evaluation.outcome,
            },
            "safety_metrics": safety_metrics,
        }
    return {
        "is_emergency": False,
        "route": "extract_merge",
        "safety_metrics": safety_metrics,
    }


def route_after_safety(state: WorkflowState) -> str:
    return "emergency_response" if state.get("is_emergency") else "extract_and_merge"


# ---------------------------------------------------------------------
# 4. EMERGENCY RESPONSE NODE
# ---------------------------------------------------------------------
def emergency_response_node(state: WorkflowState) -> dict:
    db = SessionLocal()
    try:
        emergency_data = state.get("emergency_data") or {}
        bot_reply = emergency_data.get("emergency_message") or (
            "🚨 **EMERGENCY WARNING: Immediate Medical Attention Required**\n\n"
            "Your reported symptoms indicate a potential high-risk medical condition requiring prompt emergency evaluation.\n\n"
            "Please dial 112 (National Emergency) or 108 (Ambulance), or visit the nearest hospital emergency room immediately."
        )

        TriageRepository.add_message(db, state["thread_id"], "user", state["message"], turn_id=state["turn_id"])
        TriageRepository.add_message(db, state["thread_id"], "assistant", bot_reply, turn_id=state["turn_id"])
        TriageRepository.update_session_state(
            db,
            session_id=state["thread_id"],
            clerk_user_id=state["user_id"],
            case_state=state["case_dict"],
            pending_question=None,
            status="emergency",
        )

        case = PatientCase(**state["case_dict"])
        return {
            "bot_reply": bot_reply,
            "stage": "emergency",
            "risk_level": emergency_data.get("risk_level", "emergency"),
            "confidence": 1.0,
            "sources": [],
            "assessment": None,
            "actions": [],
            "symptom_facts": case.to_summary_dict(),
            "is_complete": True,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------
# 5. EXTRACT & MERGE PATIENT FACTS NODE
# ---------------------------------------------------------------------
def extract_and_merge_node(state: WorkflowState) -> dict:
    t0 = time.time()
    case = PatientCase(**state["case_dict"])
    message = state.get("message", "")
    turn_id = state.get("turn_id", 1)

    # 1. Deterministic Greeting Check
    greeting_reply = PatientLookupEngine.check_greeting(message, case)
    if greeting_reply:
        case.record_question_asked(
            category="primary_symptom",
            question_text=greeting_reply,
            field="primary_symptom",
            turn_id=turn_id,
        )
        return {
            "case_dict": case.model_dump(),
            "greeting_reply": greeting_reply,
            "repeat_ack": None,
            "extraction_metrics": {
                "duration_s": round(time.time() - t0, 4),
                "is_greeting": True,
                "symptoms_count": len(case.symptoms),
            },
        }

    # 1b. Direct Knowledge / Educational Intent Check
    _, _, pre_intent = prepare_retrieval_query(
        message,
        case=case,
        conversation_history=state.get("recent_messages"),
    )
    if pre_intent in ("direct_knowledge", "differential_diagnosis", "out_of_corpus"):
        return {
            "case_dict": case.model_dump(),
            "greeting_reply": None,
            "repeat_ack": None,
            "query_intent": pre_intent,
            "extraction_metrics": {
                "duration_s": round(time.time() - t0, 4),
                "is_educational": True,
                "symptoms_count": len(case.symptoms),
            },
        }

    # 2. Repeated Symptom Check
    repeat_ack = PatientLookupEngine.check_already_recorded_symptom(message, case, turn_id=turn_id)
    if repeat_ack:
        return {
            "case_dict": case.model_dump(),
            "greeting_reply": None,
            "repeat_ack": repeat_ack,
            "extraction_metrics": {
                "duration_s": round(time.time() - t0, 4),
                "is_repeat": True,
                "symptoms_count": len(case.symptoms),
            },
        }

    # 3. Deterministic Answer Lookup against pending question
    answered_deterministically = PatientLookupEngine.try_deterministic_answer(message, case, turn_id=turn_id)

    # 4. Merge any newly mentioned symptoms
    symptoms_merged = PatientLookupEngine.inspect_and_merge_new_symptoms(message, case, turn_id=turn_id)

    # 5. Supplementary extraction for novel phrases if deterministic lookup did not resolve
    if not answered_deterministically and not symptoms_merged:
        extracted = SymptomExtractor.extract(message, current_facts=case.to_summary_dict())
        if extracted.symptoms:
            for sym_item in extracted.symptoms:
                case.add_or_update_symptom(
                    name=sym_item.name,
                    status=sym_item.status,
                    duration=sym_item.duration or extracted.duration,
                    severity=sym_item.severity or extracted.severity,
                    original_wording=sym_item.original_wording,
                    turn_id=turn_id,
                )
        elif extracted.primary_symptom:
            case.add_or_update_symptom(
                name=extracted.primary_symptom,
                status="present",
                duration=extracted.duration,
                severity=extracted.severity,
                original_wording=extracted.original_wording,
                turn_id=turn_id,
            )
        if extracted.duration:
            target_sym = (case.pending_target.symptom if case.pending_target else None) or case.primary_symptom.value
            if target_sym:
                case.add_or_update_symptom(name=str(target_sym), duration=extracted.duration, turn_id=turn_id)
            if case.pending_target:
                case.resolve_pending_question(answer_value=extracted.duration, turn_id=turn_id)

        if extracted.severity:
            target_sym = (case.pending_target.symptom if case.pending_target else None) or case.primary_symptom.value
            if target_sym:
                case.add_or_update_symptom(name=str(target_sym), severity=extracted.severity, turn_id=turn_id)
            if case.pending_target:
                case.resolve_pending_question(answer_value=extracted.severity, turn_id=turn_id)

        for sym in extracted.associated_symptoms:
            case.add_or_update_symptom(name=sym, status="present", turn_id=turn_id)
        for den in extracted.denied_symptoms:
            case.add_or_update_symptom(name=den, status="absent", turn_id=turn_id)

    return {
        "case_dict": case.model_dump(),
        "greeting_reply": None,
        "repeat_ack": None,
        "extraction_metrics": {
            "duration_s": round(time.time() - t0, 4),
            "symptoms_count": len(case.symptoms),
            "has_primary": bool(case.primary_symptom.value),
        },
    }


# ---------------------------------------------------------------------
# 6. ADAPTIVE INTAKE CHECK NODE
# ---------------------------------------------------------------------
def adaptive_intake_check_node(state: WorkflowState) -> dict:
    t0 = time.time()
    case = PatientCase(**state["case_dict"])
    turn_id = state.get("turn_id", 1)

    if state.get("greeting_reply"):
        return {
            "case_dict": case.model_dump(),
            "intake_complete": False,
            "next_question": state["greeting_reply"],
            "route": "ask_question",
            "question_planning_metrics": {
                "duration_s": round(time.time() - t0, 4),
                "planned": True,
                "reason": "greeting",
            },
        }

    if state.get("repeat_ack"):
        return {
            "case_dict": case.model_dump(),
            "intake_complete": False,
            "next_question": state["repeat_ack"],
            "route": "ask_question",
            "question_planning_metrics": {
                "duration_s": round(time.time() - t0, 4),
                "planned": True,
                "reason": "repeat_ack",
            },
        }

    # If the inquiry is an eligible standalone educational question, trigger direct evidence retrieval
    query_intent = state.get("query_intent")
    if not query_intent:
        _, _, query_intent = prepare_retrieval_query(
            state.get("message", ""),
            case=case,
            conversation_history=state.get("recent_messages"),
        )
    if query_intent in ("direct_knowledge", "differential_diagnosis", "out_of_corpus", "ayurvedic_guidance"):
        case.intake_status = "complete"
        case.pending_question = None
        case.pending_target = None
        return {
            "case_dict": case.model_dump(),
            "intake_complete": True,
            "next_question": None,
            "query_intent": query_intent,
            "route": "retrieve_evidence",
            "question_planning_metrics": {
                "duration_s": round(time.time() - t0, 4),
                "planned": False,
                "is_complete": True,
                "reason": "educational_query_direct_rag",
            },
        }

    # Preliminary Evidence Retrieval to support differential-driven question planning
    candidate_conditions = []
    if case.primary_symptom.value or case.symptoms:
        try:
            med_query = build_medical_query(case)
            retrieval_res = MedicalRetrievalService.retrieve(med_query, limit=3)
            for doc in retrieval_res.documents:
                title = doc.metadata.get("title", "")
                doc_id = doc.metadata.get("document_id", "")
                candidate_conditions.append({"title": title, "document_id": doc_id})
        except Exception as e:
            logger.debug(f"Preliminary evidence retrieval skipped: {e}")

    # Evaluate clinical gap and select next dynamic follow-up question
    is_complete, next_question = PatientLookupEngine.select_next_adaptive_question(
        case, turn_id=turn_id, candidate_conditions=candidate_conditions
    )
    if not is_complete and next_question:
        return {
            "case_dict": case.model_dump(),
            "intake_complete": False,
            "next_question": next_question,
            "route": "ask_question",
            "question_planning_metrics": {
                "duration_s": round(time.time() - t0, 4),
                "planned": True,
                "is_complete": False,
            },
        }

    case.intake_status = "complete"
    case.pending_question = None
    case.pending_target = None
    return {
        "case_dict": case.model_dump(),
        "intake_complete": True,
        "next_question": None,
        "route": "retrieve_evidence",
        "question_planning_metrics": {
            "duration_s": round(time.time() - t0, 4),
            "planned": False,
            "is_complete": True,
        },
    }


def route_after_intake_check(state: WorkflowState) -> str:
    return "ask_one_question" if not state.get("intake_complete") else "retrieve_medical_evidence"


# ---------------------------------------------------------------------
# 7. ASK ONE QUESTION NODE (Intake in progress)
# ---------------------------------------------------------------------
def ask_one_question_node(state: WorkflowState) -> dict:
    db = SessionLocal()
    try:
        case = PatientCase(**state["case_dict"])
        bot_reply = state["next_question"] or "What symptoms are you experiencing?"

        TriageRepository.add_message(db, state["thread_id"], "user", state["message"], turn_id=state["turn_id"])
        TriageRepository.add_message(db, state["thread_id"], "assistant", bot_reply, turn_id=state["turn_id"])
        TriageRepository.update_session_state(
            db,
            session_id=state["thread_id"],
            clerk_user_id=state["user_id"],
            case_state=case.model_dump(),
            pending_question=case.pending_question,
            status="intake",
        )

        return {
            "bot_reply": bot_reply,
            "stage": "intake",
            "risk_level": "not_assessed",
            "confidence": 0.90,
            "sources": [],
            "assessment": None,
            "actions": [],
            "symptom_facts": case.to_summary_dict(),
            "is_complete": False,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------
# 8. RETRIEVE MEDICAL EVIDENCE NODE
# ---------------------------------------------------------------------
def retrieve_medical_evidence_node(state: WorkflowState) -> dict:
    t0 = time.time()
    case = PatientCase(**state["case_dict"])
    message = state.get("message", "")
    dense_query, rerank_query, query_intent = prepare_retrieval_query(
        message,
        case=case,
        conversation_history=state.get("recent_messages"),
    )

    retrieval_result = MedicalRetrievalService.retrieve(
        dense_query=dense_query,
        limit=settings.final_k,
        rerank_query=rerank_query,
    )
    duration_s = round(time.time() - t0, 4)

    doc_ids = [
        d.metadata.get("document_id") or d.metadata.get("id")
        for d in retrieval_result.documents
        if hasattr(d, "metadata")
    ]
    return {
        "medical_query": dense_query,
        "query_intent": query_intent,
        "retrieved_documents": retrieval_result.documents,
        "retrieval_metrics": {
            "query": dense_query,
            "rerank_query": rerank_query,
            "intent": query_intent,
            "duration_s": duration_s,
            "status": retrieval_result.status,
            "chunks_retrieved": len(retrieval_result.documents),
            "document_ids": [did for did in doc_ids if did],
        },
    }


# ---------------------------------------------------------------------
# 9. CROSS-ENCODER RERANKING NODE
# ---------------------------------------------------------------------
def cross_encoder_rerank_node(state: WorkflowState) -> dict:
    # MedicalRetrievalService.retrieve internally runs cross-encoder reranking.
    docs = state.get("retrieved_documents", [])
    doc_ids = [d.metadata.get("document_id") or d.metadata.get("id") for d in docs if hasattr(d, "metadata")]
    return {
        "retrieved_documents": docs,
        "rerank_metrics": {
            "chunks_count": len(docs),
            "selected_doc_ids": [did for did in doc_ids if did],
        },
    }


# ---------------------------------------------------------------------
# 10. EVIDENCE CONTEXT ASSEMBLY NODE
# ---------------------------------------------------------------------
def evidence_context_assembly_node(state: WorkflowState) -> dict:
    docs = state.get("retrieved_documents", [])
    evidence_context = assemble_medical_context(docs)
    return {
        "evidence_context": {
            "formatted_context": evidence_context.formatted_context,
            "sources": evidence_context.sources,
            "total_tokens_approx": evidence_context.total_tokens_approx,
        }
    }


# ---------------------------------------------------------------------
# 11. DIFFERENTIAL ASSESSMENT NODE
# ---------------------------------------------------------------------
def differential_assessment_node(state: WorkflowState) -> dict:
    case = PatientCase(**state["case_dict"])
    raw_ctx = state.get("evidence_context", {}) or {}
    evidence_context = AssembledEvidenceContext(
        formatted_context=raw_ctx.get("formatted_context", ""),
        sources=raw_ctx.get("sources", []),
        total_tokens_approx=raw_ctx.get("total_tokens_approx", 0),
    )
    query_intent = state.get("query_intent") or "symptom_triage"
    user_msg = state.get("message", "")

    if query_intent in ("direct_knowledge", "differential_diagnosis", "out_of_corpus"):
        direct_resp = EvidenceGroundedSynthesizer.generate_direct_knowledge_response(
            user_query=user_msg,
            context=evidence_context,
        )
        return {
            "assessment_result": {
                "direct_response": direct_resp,
                "is_direct": True,
                "sources": raw_ctx.get("sources", []),
            }
        }
    else:
        assessment = EvidenceGroundedSynthesizer.synthesize(case, evidence_context)
        return {
            "assessment_result": assessment.model_dump(),
        }


# ---------------------------------------------------------------------
# 12. CITATION VALIDATION NODE
# ---------------------------------------------------------------------
def citation_validation_node(state: WorkflowState) -> dict:
    assessment_data = state.get("assessment_result", {}) or {}
    raw_ctx = state.get("evidence_context", {}) or {}
    sources = raw_ctx.get("sources", [])
    valid_source_ids = {s.get("document_id") for s in sources if s.get("document_id")}
    valid_source_ids.update({f"[{s.get('document_id')}]" for s in sources if s.get("document_id")})
    valid_source_ids.update({f"[{s.get('ref_id')}]" for s in sources if s.get("ref_id")})

    summary_text = assessment_data.get("direct_response") or assessment_data.get("case_summary", "")
    val_res = CitationValidator.validate(summary_text, sources)

    return {
        "validated_citations": list(valid_source_ids),
        "citation_metrics": {
            "valid_citations_count": len(val_res.referenced_sources),
            "unsupported_citations_count": len(val_res.unsupported_citations),
            "is_valid": val_res.is_valid,
        },
    }


# ---------------------------------------------------------------------
# 13. PERSIST ASSESSMENT NODE
# ---------------------------------------------------------------------
def persist_assessment_node(state: WorkflowState) -> dict:
    db = SessionLocal()
    try:
        assessment_data = state.get("assessment_result", {}) or {}
        raw_ctx = state.get("evidence_context", {}) or {}
        source_ids = [s["document_id"] for s in raw_ctx.get("sources", []) if "document_id" in s]

        persisted = TriageRepository.save_assessment(
            db=db,
            session_id=state["thread_id"],
            user_id=state["user_id"],
            assessment_json=assessment_data,
            evidence_source_ids=source_ids,
            assessment_version="2.0.0",
            safety_ruleset_version=settings.safety_ruleset_version,
            rag_configuration_version="2.0.0",
        )
        return {
            "persisted_assessment_id": persisted.id,
        }
    except Exception as e:
        logger.error("Failed to persist assessment: %s", e)
        return {
            "persisted_assessment_id": None,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------
# 14. RETURN ASSESSMENT + TWO ACTIONS NODE
# ---------------------------------------------------------------------
def return_assessment_node(state: WorkflowState) -> dict:
    db = SessionLocal()
    try:
        case = PatientCase(**state["case_dict"])
        assessment_data = state.get("assessment_result", {}) or {}
        raw_ctx = state.get("evidence_context", {}) or {}

        if assessment_data.get("is_direct"):
            bot_reply = assessment_data.get("direct_response", "")
            sources = [
                {
                    "title": s.get("title", "Clinical Reference"),
                    "id": s.get("document_id", "REF-01"),
                    "ref_id": s.get("ref_id", ""),
                    "tag": s.get("publisher", "WHO")[:15],
                    "url": s.get("url"),
                    "score": s.get("score"),
                }
                for s in raw_ctx.get("sources", [])
            ]
            actions = [
                {
                    "id": "GET_AYURVEDIC_GUIDANCE",
                    "label": "Explore Ayurvedic guidance",
                    "condition_id": "general-guidance",
                },
                {
                    "id": "FIND_NEARBY_CLINICS",
                    "label": "Find nearby clinics",
                    "condition_id": "general-guidance",
                },
            ]
            return {
                "bot_reply": bot_reply,
                "stage": "complete",
                "risk_level": "informational",
                "confidence": 0.95,
                "sources": sources,
                "assessment": None,
                "actions": actions,
                "symptom_facts": case.to_summary_dict(),
                "is_complete": True,
            }

        # Build clean user-facing assessment response
        reply_parts = [f"**Clinical Triage Assessment:**\n{assessment_data.get('case_summary', '')}\n"]

        conditions = assessment_data.get("possible_conditions", [])
        if conditions:
            reply_parts.append("**Possible Differential Conditions:**")
            for cond in conditions:
                cites = " ".join(cond.get("supporting_evidence_ids", []))
                rec = f" — *Care Setting: {cond.get('recommended_care_setting')}*" if cond.get("recommended_care_setting") else ""
                reply_parts.append(f"- **{cond.get('name')}**: {cond.get('explanation')} {cites}{rec}".strip())
                if cond.get("findings_against"):
                    reply_parts.append(f"  - *Conflicting Findings*: {cond.get('findings_against')}")
                if cond.get("uncertainties"):
                    reply_parts.append(f"  - *Diagnostic Uncertainties*: {cond.get('uncertainties')}")
            reply_parts.append("")

        recommended_actions = assessment_data.get("recommended_actions", [])
        if recommended_actions:
            reply_parts.append("**Recommended Evidence-Based Care:**")
            for act in recommended_actions:
                cites = " ".join(act.get("supporting_evidence_ids", []))
                reply_parts.append(f"- {act.get('action')} ({act.get('rationale')}) {cites}".strip())
            reply_parts.append("")

        warning_signs = assessment_data.get("warning_signs", [])
        if warning_signs:
            reply_parts.append("**⚠️ Warning Signs (Seek Immediate Medical Care if Experienced):**")
            for sign in warning_signs:
                reply_parts.append(f"- {sign}")
            reply_parts.append("")

        limitations = assessment_data.get("evidence_limitations", [])
        if limitations:
            reply_parts.append("**Clinical Evidence Limitations:**")
            for lim in limitations:
                reply_parts.append(f"- {lim}")
            reply_parts.append("")

        reply_parts.append(f"*{assessment_data.get('disclaimer', 'BluCare+ is an AI clinical decision-support tool. Consult a licensed physician for medical diagnosis.')}*")
        bot_reply = "\n".join(reply_parts)

        # Build sources list
        sources = [
            {
                "title": s.get("title", "Clinical Reference"),
                "id": s.get("document_id", "REF-01"),
                "ref_id": s.get("ref_id", ""),
                "tag": s.get("publisher", "WHO")[:15],
                "url": s.get("url"),
                "score": s.get("score"),
            }
            for s in raw_ctx.get("sources", [])
        ]

        # Present the two structured actions for the top condition
        primary_cond_id = conditions[0]["condition_id"] if conditions else "general-assessment"
        actions = [
            {
                "id": "GET_AYURVEDIC_GUIDANCE",
                "label": "Explore Ayurvedic guidance",
                "condition_id": primary_cond_id,
            },
            {
                "id": "FIND_NEARBY_CLINICS",
                "label": "Find nearby clinics",
                "condition_id": primary_cond_id,
            },
        ]

        structured_assessment = {
            "case_summary": assessment_data.get("case_summary", ""),
            "possible_conditions": conditions,
            "recommended_actions": recommended_actions,
            "warning_signs": warning_signs,
            "sources": sources,
            "evidence_limitations": assessment_data.get("evidence_limitations", []),
        }

        # Save assistant message & update session in database
        TriageRepository.add_message(db, state["thread_id"], "user", state["message"], turn_id=state["turn_id"])
        TriageRepository.add_message(db, state["thread_id"], "assistant", bot_reply, turn_id=state["turn_id"])
        TriageRepository.update_session_state(
            db,
            session_id=state["thread_id"],
            clerk_user_id=state["user_id"],
            case_state=case.model_dump(),
            pending_question=None,
            status="completed",
        )

        return {
            "bot_reply": bot_reply,
            "stage": "post_prediction",
            "risk_level": "low",
            "confidence": 0.90 if not assessment_data.get("is_insufficient_evidence") else 0.50,
            "sources": sources,
            "assessment": structured_assessment,
            "actions": actions,
            "symptom_facts": case.to_summary_dict(),
            "is_complete": True,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------
# 15. POST-ASSESSMENT ACTION A: AYURVEDIC GUIDANCE NODE
# ---------------------------------------------------------------------
def ayurvedic_guidance_node(state: WorkflowState) -> dict:
    db = SessionLocal()
    try:
        session = TriageRepository.get_session(db, state["thread_id"], clerk_user_id=state["user_id"])
        case = PatientCase(**(session.case_state if session else {}))
        case.turn_count += 1
        turn_id = case.turn_count
        condition_id = state.get("condition_id")
        # Condition ID Validation: verify requested condition belongs to this session's assessment
        latest_assessment = TriageRepository.get_latest_assessment(db, state["thread_id"])
        if not latest_assessment or not latest_assessment.assessment_json:
            raise HTTPException(
                status_code=400,
                detail="No completed clinical assessment found for this session. Complete triage intake first.",
            )

        conds = latest_assessment.assessment_json.get("possible_conditions", [])
        if not condition_id and conds:
            condition_id = conds[0].get("condition_id")

        valid_conditions = [c.get("condition_id") for c in conds]
        condition_name = None
        for c in conds:
            if c.get("condition_id") == condition_id:
                condition_name = c.get("name")
                break

        if not condition_name or condition_id not in valid_conditions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid condition_id '{condition_id}'. Valid conditions for this assessment are: {', '.join(valid_conditions)}",
            )

        # Retrieve relevant Ayurvedic evidence
        query = f"Ayurvedic clinical guidance for {condition_name} traditional diet herbal remedies"
        retrieval_res = MedicalRetrievalService.retrieve(query, limit=3)
        ayu_docs = [
            d for d in retrieval_res.documents
            if d.metadata.get("clinical_topic", "").startswith("Complementary") or "AYU" in d.metadata.get("document_id", "")
        ]

        if not ayu_docs:
            # Fallback to any retrieved documents if specific topic filter empty
            ayu_docs = retrieval_res.documents[:2]

        context_text = "\n\n".join([f"[{d.metadata.get('document_id', 'AYU-REF')}] {d.page_content}" for d in ayu_docs])
        source_ids = [d.metadata.get("document_id", "AYU-REF") for d in ayu_docs]

        guidance = AyurvedicSynthesizer.synthesize_guidance(
            condition_id=condition_id,
            condition_name=condition_name,
            case=case,
            context_text=context_text,
            source_ids=source_ids,
        )

        reply_parts = [
            f"### 🌿 Ayurvedic & Complementary Health Guidance: {guidance.condition_name}",
            f"**Traditional Classification**: {guidance.traditional_classification}\n",
            "**Dietary & Lifestyle Supportive Measures (Langhana & Care):**",
        ]
        for diet in guidance.dietary_and_lifestyle_care:
            reply_parts.append(f"- {diet}")

        if guidance.traditional_herbal_wellness:
            reply_parts.append("\n**Traditional Herbal Wellness (Home Decoctions & Teas):**")
            for herb in guidance.traditional_herbal_wellness:
                reply_parts.append(f"- {herb}")

        reply_parts.append("\n**Safety, Contraindications & Drug-Herbal Interactions:**")
        for contra in guidance.safety_and_contraindications:
            reply_parts.append(f"- ⚠️ {contra}")

        if guidance.citations:
            reply_parts.append(f"\n**Verified Knowledge Sources**: {', '.join(guidance.citations)}")

        if guidance.evidence_limitations:
            reply_parts.append("\n**Evidence Limitations & Clinical Transparency:**")
            for lim in guidance.evidence_limitations:
                reply_parts.append(f"- {lim}")

        reply_parts.append(f"\n*{guidance.clinical_disclaimer}*")
        bot_reply = "\n".join(reply_parts)

        sources = [
            {
                "title": d.metadata.get("title", "Ayurvedic Pharmacopoeia"),
                "id": d.metadata.get("document_id", "AYU-01"),
                "tag": d.metadata.get("publisher", "Ministry of AYUSH")[:15],
            }
            for d in ayu_docs
        ]

        TriageRepository.add_message(db, state["thread_id"], "user", f"[Selected Action: Explore Ayurvedic Guidance for {condition_name}]", turn_id=turn_id)
        TriageRepository.add_message(db, state["thread_id"], "assistant", bot_reply, turn_id=turn_id)

        return {
            "bot_reply": bot_reply,
            "stage": "post_prediction",
            "risk_level": "low",
            "confidence": 0.90,
            "sources": sources,
            "assessment": None,
            "actions": [],
            "symptom_facts": case.to_summary_dict(),
            "is_complete": True,
            "ayurvedic_guidance": {
                "condition_name": guidance.condition_name,
                "traditional_classification": guidance.traditional_classification,
                "dietary_and_lifestyle_care": guidance.dietary_and_lifestyle_care,
                "traditional_herbal_wellness": guidance.traditional_herbal_wellness,
                "safety_and_contraindications": guidance.safety_and_contraindications,
                "citations": guidance.citations,
                "evidence_limitations": guidance.evidence_limitations,
                "clinical_disclaimer": guidance.clinical_disclaimer,
            },
        }
    finally:
        db.close()


# ---------------------------------------------------------------------
# 16. POST-ASSESSMENT ACTION B: FIND NEARBY CLINICS NODE
# ---------------------------------------------------------------------
def facilities_service_node(state: WorkflowState) -> dict:
    db = SessionLocal()
    try:
        session = TriageRepository.get_session(db, state["thread_id"], clerk_user_id=state["user_id"])
        case = PatientCase(**(session.case_state if session else {}))
        case.turn_count += 1
        turn_id = case.turn_count
        condition_id = state.get("condition_id")

        # Identify condition if present, else default gracefully to general medical care
        latest_assessment = TriageRepository.get_latest_assessment(db, state["thread_id"])
        condition_name = "general healthcare evaluation"
        if latest_assessment and latest_assessment.assessment_json:
            conds = latest_assessment.assessment_json.get("possible_conditions", [])
            if not condition_id and conds:
                condition_id = conds[0].get("condition_id")
            for c in conds:
                if c.get("condition_id") == condition_id:
                    condition_name = c.get("name") or condition_name
                    break
            if condition_name == "general healthcare evaluation" and conds:
                condition_name = conds[0].get("name", "general healthcare evaluation")

        lat = state.get("latitude")
        lng = state.get("longitude")

        # Strict coordinate handling: Never silently default to Bengaluru if coords are missing
        if lat is None or lng is None:
            gmaps_search_url = "https://www.google.com/maps/search/?api=1&query=clinics+and+hospitals+near+me"
            bot_reply = (
                f"### 📍 Location Permission Required for Nearby Facility Discovery\n\n"
                f"To find genuine clinics and hospitals near you for **{condition_name}**, BluCare+ requires your location coordinates.\n\n"
                f"1. **Allow Location**: Please ensure location access is enabled in your browser, then retry finding nearby clinics.\n"
                f"2. **Direct Search**: You can also search directly on Google Maps: [🔍 Search Nearby Clinics & Hospitals on Google Maps]({gmaps_search_url})\n\n"
                f"*BluCare+ prioritizes user privacy and never stores your exact GPS coordinates without your permission.*"
            )
            TriageRepository.add_message(db, state["thread_id"], "user", f"[Selected Action: Find Nearby Clinics for {condition_name}]", turn_id=turn_id)
            TriageRepository.add_message(db, state["thread_id"], "assistant", bot_reply, turn_id=turn_id)
            db.commit()
            return {
                "bot_reply": bot_reply,
                "facilities": [],
                "external_search": {
                    "google_maps_clinics": gmaps_search_url,
                    "google_maps_hospitals": gmaps_search_url,
                },
                "status": "location_required",
            }

        service = FacilitiesService()
        nearby_res = service.search_nearby(
            lat=lat,
            lng=lng,
            radius=5000,
            limit=5,
            category="all",
            condition_name=condition_name,
        )

        top_5_facilities = (nearby_res.facilities or [])[:5]

        reply_parts = [
            f"### 🏥 Top 5 Nearest Healthcare Facilities",
            f"Searching around location ({lat:.4f}° N, {lng:.4f}° E) for medical facilities regarding **{condition_name}**:\n",
        ]

        if top_5_facilities:
            reply_parts.append("**Verified Facilities (Ranked Nearest First):**\n")
            for idx, fac in enumerate(top_5_facilities, 1):
                dist = format_distance(fac.distance_meters)
                cat_tag = f" [{fac.category.title()}]" if fac.category else ""
                phone = f" | 📞 {fac.phone}" if fac.phone else ""
                addr = f"\n   - *Address*: {fac.address}" if fac.address else ""
                nav_link = f" [🗺️ Directions]({fac.directions_url or fac.maps_url})" if (fac.directions_url or fac.maps_url) else ""
                reply_parts.append(f"{idx}. **{fac.name}**{cat_tag} (~{dist} away{phone}){addr}{nav_link}\n")
        else:
            reply_parts.append(
                "No verified medical facilities were discovered within 5 km of your coordinates. "
                "You can explore broader Google Maps listings below.\n"
            )

        # Dual Universal Google Maps Search links for broader local search (privacy: NO symptoms sent to Google Maps)
        gmaps_clinics_url = build_google_maps_search_url(lat, lng, "clinics")
        gmaps_hospitals_url = build_google_maps_search_url(lat, lng, "hospitals")
        reply_parts.append("\n**Explore Verified Local Listings on Google Maps:**")
        reply_parts.append(f"- [🔍 Search Nearby Clinics on Google Maps]({gmaps_clinics_url})")
        reply_parts.append(f"- [🏥 Search Nearby Hospitals on Google Maps]({gmaps_hospitals_url})\n")
        reply_parts.append("*Straight-line distances are approximate. Tap Directions for live GPS turn-by-turn navigation.*")

        bot_reply = "\n".join(reply_parts)

        TriageRepository.add_message(db, state["thread_id"], "user", f"[Selected Action: Find Nearby Clinics for {condition_name}]", turn_id=turn_id)
        TriageRepository.add_message(db, state["thread_id"], "assistant", bot_reply, turn_id=turn_id)

        facilities_data = [
            {
                "id": getattr(fac, "id", None) or f"fac_{idx}",
                "name": fac.name or f"Verified {fac.category.title()}",
                "category": fac.category,
                "latitude": fac.latitude,
                "longitude": fac.longitude,
                "distance_meters": fac.distance_meters,
                "distance_formatted": format_distance(fac.distance_meters),
                "address": fac.address,
                "phone": fac.phone,
                "opening_hours": fac.opening_hours,
                "emergency": fac.emergency,
                "specialty": getattr(fac, "specialty", None),
                "rating": getattr(fac, "rating", None),
                "review_count": getattr(fac, "review_count", None),
                "maps_url": fac.maps_url,
                "directions_url": fac.directions_url or build_google_maps_directions_url(fac.latitude, fac.longitude),
            }
            for idx, fac in enumerate(top_5_facilities, 1)
        ]
        external_search_data = {
            "google_maps_clinics": gmaps_clinics_url,
            "google_maps_hospitals": gmaps_hospitals_url,
            "google_maps": {
                "clinics_url": gmaps_clinics_url,
                "hospitals_url": gmaps_hospitals_url,
            },
        }

        return {
            "bot_reply": bot_reply,
            "stage": "post_prediction",
            "risk_level": "low",
            "confidence": 0.95,
            "sources": [],
            "assessment": None,
            "actions": [],
            "symptom_facts": case.to_summary_dict(),
            "is_complete": True,
            "facilities": facilities_data,
            "external_search": external_search_data,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------
# 17. BUILD & COMPILE COMPLETE WORKFLOW
# ---------------------------------------------------------------------
def build_triage_graph():
    workflow = StateGraph(WorkflowState)

    # Core nodes
    workflow.add_node("entry_router", entry_router_node)
    workflow.add_node("load_patient_context", load_patient_context_node)
    workflow.add_node("safety_assessment", safety_assessment_node)
    workflow.add_node("emergency_response", emergency_response_node)
    workflow.add_node("extract_and_merge", extract_and_merge_node)
    workflow.add_node("adaptive_intake_check", adaptive_intake_check_node)
    workflow.add_node("ask_one_question", ask_one_question_node)

    # Medical RAG & Assessment nodes
    workflow.add_node("retrieve_medical_evidence", retrieve_medical_evidence_node)
    workflow.add_node("cross_encoder_rerank", cross_encoder_rerank_node)
    workflow.add_node("evidence_context_assembly", evidence_context_assembly_node)
    workflow.add_node("differential_assessment", differential_assessment_node)
    workflow.add_node("citation_validation", citation_validation_node)
    workflow.add_node("persist_assessment", persist_assessment_node)
    workflow.add_node("return_assessment", return_assessment_node)

    # Post-assessment action nodes
    workflow.add_node("ayurvedic_guidance", ayurvedic_guidance_node)
    workflow.add_node("facilities_service", facilities_service_node)

    # Graph entry and conditional branching
    workflow.set_entry_point("entry_router")

    workflow.add_conditional_edges(
        "entry_router",
        route_from_entry,
        {
            "ayurvedic": "ayurvedic_guidance",
            "clinics": "facilities_service",
            "load_context": "load_patient_context",
        },
    )

    workflow.add_edge("load_patient_context", "safety_assessment")

    workflow.add_conditional_edges(
        "safety_assessment",
        route_after_safety,
        {
            "emergency_response": "emergency_response",
            "extract_and_merge": "extract_and_merge",
        },
    )

    workflow.add_edge("emergency_response", END)
    workflow.add_edge("extract_and_merge", "adaptive_intake_check")

    workflow.add_conditional_edges(
        "adaptive_intake_check",
        route_after_intake_check,
        {
            "ask_one_question": "ask_one_question",
            "retrieve_medical_evidence": "retrieve_medical_evidence",
        },
    )

    workflow.add_edge("ask_one_question", END)

    # RAG linear chain
    workflow.add_edge("retrieve_medical_evidence", "cross_encoder_rerank")
    workflow.add_edge("cross_encoder_rerank", "evidence_context_assembly")
    workflow.add_edge("evidence_context_assembly", "differential_assessment")
    workflow.add_edge("differential_assessment", "citation_validation")
    workflow.add_edge("citation_validation", "persist_assessment")
    workflow.add_edge("persist_assessment", "return_assessment")
    workflow.add_edge("return_assessment", END)

    # Post-assessment actions terminate at END
    workflow.add_edge("ayurvedic_guidance", END)
    workflow.add_edge("facilities_service", END)

    # State checkpointing
    try:
        import sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver
        sqlite_conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False, timeout=30.0)
        sqlite_conn.execute("PRAGMA journal_mode=WAL;")
        sqlite_conn.execute("PRAGMA busy_timeout=30000;")
        checkpointer = SqliteSaver(sqlite_conn)
        logger.info("LangGraph workflow checkpointer: SQLite (checkpoints.sqlite with WAL).")
    except Exception:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        logger.info("LangGraph workflow checkpointer: MemorySaver.")

    return workflow.compile(checkpointer=checkpointer)


# Global compiled workflow instance
compiled_triage_graph = build_triage_graph()
compiled_graph = compiled_triage_graph  # Backwards compatibility alias
