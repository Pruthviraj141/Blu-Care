"""
Test suite for Section 11 of ragas2.md: Real User Testing Scenarios.
Verifies:
1. Simple medical question (direct evidence-grounded answer).
2. Same question in different words (semantic invariance).
3. Common spelling mistakes (deterministic typo cleanup).
4. Everyday symptom descriptions (colloquial metaphor handling).
5. Multi-turn follow-up questions (conversational coreference resolution).
6. Unknown medical conditions (honest out-of-corpus handling).
7. Insufficient evidence (explicit clinical abstention without hallucination).
8. Emergency symptoms (deterministic immediate emergency short-circuit).
9. Citation validity (independent verification against retrieved documents).
10. Redis hit and bypass behavior (educational cached, emergencies & assessments bypassed).
11. Session resumption and state continuity.
"""

import pytest
from app.core.config import settings
from app.core.session_service import SessionService
from app.services.safety_engine import SafetyEngine
from app.rag.query_builder import prepare_retrieval_query, clean_typos, resolve_coreference
from app.rag.retrieval_service import MedicalRetrievalService
from app.rag.citation_validator import CitationValidator
from app.services.semantic_cache import SemanticCacheService

settings.allow_dev_auth = True
settings.app_env = "testing"


def test_scenario_1_simple_medical_question():
    """Scenario 1: Simple medical question produces direct evidence-grounded answer."""
    session_id, reply = SessionService.start_session("What is migraine?", user_id="user_test_1")
    assert reply, "Expected non-empty response"
    reply_lower = reply.lower()
    assert "migraine" in reply_lower
    assert any(term in reply_lower for term in ["neurological", "throbbing", "pulsating", "headache"])
    # Should not fabricate a patient triage note
    assert "patient reports" not in reply_lower


def test_scenario_2_same_question_different_words():
    """Scenario 2: Same question expressed in different words retrieves consistent evidence."""
    q1 = "What is migraine?"
    q2 = "Can you explain what happens during a migraine attack?"

    dense1, rerank1, intent1 = prepare_retrieval_query(q1)
    dense2, rerank2, intent2 = prepare_retrieval_query(q2)

    assert intent1 == "direct_knowledge"
    assert intent2 == "direct_knowledge"

    res1 = MedicalRetrievalService.retrieve(dense_query=dense1, rerank_query=rerank1)
    res2 = MedicalRetrievalService.retrieve(dense_query=dense2, rerank_query=rerank2)

    docs1 = [d.metadata.get("document_id") for d in res1.documents]
    docs2 = [d.metadata.get("document_id") for d in res2.documents]

    assert "MED-MIGRAINE-WITHOUT-AURA-02" in docs1
    assert "MED-MIGRAINE-WITHOUT-AURA-02" in docs2


def test_scenario_3_common_spelling_mistakes():
    """Scenario 3: Common spelling mistakes and medical typos are cleaned deterministically."""
    typo_q = "What is migrane and nausia and fevr?"
    cleaned = clean_typos(typo_q)
    assert "migraine" in cleaned
    assert "nausea" in cleaned
    assert "fever" in cleaned


def test_scenario_4_everyday_symptom_descriptions():
    """Scenario 4: Colloquial symptom metaphors (squeezing, tight band) map to clinical guidelines."""
    dense, rerank, intent = prepare_retrieval_query("My head feels like someone is squeezing it.")
    assert intent == "symptom_triage"
    res = MedicalRetrievalService.retrieve(dense_query=dense, rerank_query=rerank)
    docs = [d.metadata.get("document_id") for d in res.documents]
    assert "MED-TENSION-HEADACHE-01" in docs


def test_scenario_5_multi_turn_follow_up():
    """Scenario 5: Multi-turn follow-up ('Why does it happen?') resolves pronouns correctly."""
    history = [
        {"role": "user", "content": "What is migraine?"},
        {"role": "assistant", "content": "Migraine is a recurrent neurological disorder typically presenting with unilateral throbbing headache."},
    ]
    resolved = resolve_coreference("Why does it happen?", history=history)
    assert "migraine" in resolved.lower()

    dense, rerank, intent = prepare_retrieval_query("Why does it happen?", conversation_history=history)
    assert intent == "direct_knowledge"
    res = MedicalRetrievalService.retrieve(dense_query=dense, rerank_query=rerank)
    docs = [d.metadata.get("document_id") for d in res.documents]
    assert "MED-MIGRAINE-WITHOUT-AURA-02" in docs


def test_scenario_6_unknown_medical_conditions():
    """Scenario 6: Unknown or unverified conditions are identified as out-of-corpus."""
    dense, rerank, intent = prepare_retrieval_query(
        "I have severe pain in my lower right abdomen near the hip bone, with nausea and loss of appetite."
    )
    assert intent == "out_of_corpus"


def test_scenario_7_insufficient_evidence_abstention():
    """Scenario 7: Explicit honest abstention when clinical evidence is unavailable."""
    from app.rag.synthesizer import EvidenceGroundedSynthesizer
    reply = EvidenceGroundedSynthesizer.generate_insufficient_evidence_response("acute appendicitis lower abdomen")
    assert "not available in the current BluCare+ medical knowledge base" in reply
    assert "consult a licensed physician" in reply.lower()


def test_scenario_8_emergency_symptoms():
    """Scenario 8: Life-threatening emergency symptoms trigger deterministic safety warning."""
    eval_res = SafetyEngine.evaluate("I suddenly got the worst headache of my life 10 minutes ago, like an explosion in my brain, and my neck is stiffening up.")
    assert eval_res.is_emergency is True
    assert "108" in eval_res.emergency_message or "112" in eval_res.emergency_message or "emergency" in eval_res.emergency_message.lower()


def test_scenario_9_citation_validation():
    """Scenario 9: Citation validator flags unsupported citations and verifies valid ones."""
    sources = [{"ref_id": "S1", "document_id": "MED-TENSION-HEADACHE-01"}]
    
    # Valid citation
    valid_res = CitationValidator.validate("Tension headache causes dull pain [MED-TENSION-HEADACHE-01].", sources)
    assert valid_res.is_valid is True
    assert len(valid_res.unsupported_citations) == 0

    # Invalid citation
    invalid_res = CitationValidator.validate("Tension headache causes dull pain [MED-FAKE-99].", sources)
    assert invalid_res.is_valid is False
    assert "[MED-FAKE-99]" in invalid_res.unsupported_citations


def test_scenario_10_redis_cache_bypass_and_hit():
    """Scenario 10: General educational queries are eligible for caching; emergencies bypass."""
    # Emergency bypass
    is_emerg_eligible, emerg_reason = SemanticCacheService.is_cache_eligible(
        "I have the worst headache of my life, explosion in my brain",
    )
    assert is_emerg_eligible is False
    assert "emergency" in emerg_reason.lower()

    # Educational eligible
    is_edu_eligible, edu_reason = SemanticCacheService.is_cache_eligible(
        "What is migraine?",
    )
    assert is_edu_eligible is True


def test_scenario_11_session_resumption():
    """Scenario 11: Session resumption preserves conversation continuity across turns."""
    session_id, reply1 = SessionService.start_session("I have had a mild headache for 2 days", user_id="user_resume_1")
    assert session_id

    # Turn 2
    res2 = SessionService.process_message(thread_id=session_id, message="no nausea or vomiting", user_id="user_resume_1")
    assert res2.get("message")
    facts = res2.get("symptom_facts", {}).get("symptoms", {})
    assert "headache" in facts
