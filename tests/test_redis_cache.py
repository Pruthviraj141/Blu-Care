"""
Comprehensive Test Suite for BluCare+ Redis Semantic Caching.
Verifies all 13 required scenarios from evaluation/redis.md:
1. First eligible general question -> cache miss.
2. Repeated identical general question -> cache hit.
3. Semantically similar eligible question -> cache hit when match is close.
4. Different medical topic -> cache miss.
5. Similar wording but different clinical meaning -> cache miss.
6. Active patient assessment -> cache bypass.
7. Personalized dosage question -> cache bypass.
8. Emergency-related question -> cache bypass.
9. Patient history or sensitive context -> cache bypass.
10. Expired cache entry -> cache miss.
11. Changed corpus or prompt version -> invalid entry is not reused.
12. Redis unavailable -> existing application continues to function.
13. Invalid cached metadata or citations -> cache miss.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.services.semantic_cache import SemanticCacheService
from app.services.patient_case import PatientCase
from app.core.session_service import SessionService


@pytest.fixture(autouse=True)
def clean_redis_cache():
    """Ensure clean cache before and after each test."""
    SemanticCacheService.clear_cache()
    yield
    SemanticCacheService.clear_cache()


def test_scenario_01_first_eligible_question_miss():
    """1. First eligible general question results in a cache miss."""
    query = "What is migraine?"
    is_eligible, reason = SemanticCacheService.is_cache_eligible(query)
    assert is_eligible, f"Expected eligible, got {reason}"

    hit = SemanticCacheService.lookup(query)
    assert hit is None


def test_scenario_02_repeated_identical_question_hit():
    """2. Repeated identical general question returns a cache hit."""
    query = "What is migraine?"
    response = "Migraine is a recurrent neurological disorder causing throbbing head pain."
    sources = [{"document_id": "MED-MIGRAINE-01", "title": "Migraine Protocol", "publisher": "BMJ"}]

    stored = SemanticCacheService.store(query, response, sources)
    assert stored

    hit = SemanticCacheService.lookup(query)
    assert hit is not None
    assert hit["response"] == response
    assert hit["distance"] <= settings.redis_cache_distance_threshold
    assert len(hit["sources"]) == 1


def test_scenario_03_semantically_similar_question_hit():
    """3. Semantically similar eligible question hits cache when distance is within threshold."""
    query = "What is migraine headache?"
    response = "Migraine is a recurrent headache condition with sensory disturbances."
    sources = [{"document_id": "MED-MIGRAINE-01", "title": "Migraine Overview"}]

    SemanticCacheService.store(query, response, sources)

    # Paraphrased version
    paraphrase = "What is a migraine headache?"
    hit = SemanticCacheService.lookup(paraphrase)
    assert hit is not None
    assert hit["response"] == response
    assert hit["distance"] <= settings.redis_cache_distance_threshold


def test_scenario_04_different_medical_topic_miss():
    """4. Different medical topic results in a cache miss."""
    SemanticCacheService.store(
        "What is migraine?",
        "Migraine description",
        [{"document_id": "MED-01"}]
    )

    hit = SemanticCacheService.lookup("What is dehydration?")
    assert hit is None


def test_scenario_05_similar_words_different_clinical_meaning_miss():
    """5. Similar words with different clinical meaning must not falsely hit cache."""
    # "viral pharyngitis" vs "streptococcal pharyngitis"
    SemanticCacheService.store(
        "What is viral pharyngitis?",
        "Viral pharyngitis is a self-limiting inflammation of the pharynx caused by viruses.",
        [{"document_id": "MED-VIRAL-PHARYNGITIS"}]
    )

    hit = SemanticCacheService.lookup("What is streptococcal pharyngitis?")
    assert hit is None, f"Expected cache miss for different clinical condition, but got hit: {hit}"


def test_scenario_06_active_patient_assessment_bypass():
    """6. Active patient assessment (symptoms present, turn > 1) always bypasses cache."""
    case = PatientCase()
    case.add_or_update_symptom("fever", status="present", duration="3 days", severity="moderate")

    is_eligible, reason = SemanticCacheService.is_cache_eligible("What is fever?", case=case, turn_id=2)
    assert not is_eligible
    assert reason in ("active_patient_assessment", "active_conversation_turn")


def test_scenario_07_personalized_dosage_question_bypass():
    """7. Medication dosage and prescription questions must bypass cache."""
    queries = [
        "Which paracetamol dosage should I take?",
        "How many mg of ibuprofen can I take?",
        "Can you prescribe me an antibiotic dose?",
    ]
    for q in queries:
        is_eligible, reason = SemanticCacheService.is_cache_eligible(q)
        assert not is_eligible, f"Query '{q}' should be bypassed"
        assert reason in ("medication_dosage_request", "personal_patient_pronouns")


def test_scenario_08_emergency_question_bypass():
    """8. Emergency and red-flag questions must always bypass response caching."""
    queries = [
        "I have severe crushing chest pain and sweating",
        "Sudden numbness on one side of face and arm weakness",
        "Severe shortness of breath and coughing blood",
    ]
    for q in queries:
        is_eligible, reason = SemanticCacheService.is_cache_eligible(q)
        assert not is_eligible, f"Emergency query '{q}' must be bypassed"
        assert reason in ("emergency_safety_trigger", "personal_patient_pronouns", "patient_severity_qualifier")


def test_scenario_09_patient_history_or_sensitive_context_bypass():
    """9. Personal medical history, pregnancy, allergies, or pediatric contexts bypass cache."""
    queries = [
        "What should a pregnant patient do for mild headache?",
        "I have hypertension and renal disease, what can cause fever?",
        "My 6-month-old infant has mild fever",
    ]
    for q in queries:
        is_eligible, reason = SemanticCacheService.is_cache_eligible(q)
        assert not is_eligible, f"Sensitive query '{q}' must be bypassed"
        assert reason in (
            "personal_condition_context",
            "personal_patient_pronouns",
            "patient_temporal_onset",
            "patient_severity_qualifier",
        )


def test_scenario_10_expired_cache_entry_miss():
    """10. Expired cache entry (TTL passed) results in a cache miss and is removed."""
    query = "What is tension headache?"
    SemanticCacheService.store(query, "Tension headache info", [{"document_id": "MED-TH-01"}])

    client = SemanticCacheService.get_redis_client()
    assert client is not None

    keys = client.keys(f"blucare:semcache:*")
    assert len(keys) == 1

    # Artificially set expiration to the past
    client.hset(keys[0], "expires_at", str(time.time() - 100))

    hit = SemanticCacheService.lookup(query)
    assert hit is None


def test_scenario_11_changed_corpus_or_prompt_version_miss():
    """11. Changed corpus version or prompt version invalidates cached entry."""
    query = "What is viral gastroenteritis?"
    SemanticCacheService.store(query, "Gastroenteritis info", [{"document_id": "MED-GE-01"}])

    # Lookup works initially
    hit = SemanticCacheService.lookup(query)
    assert hit is not None

    # Alter corpus version in settings
    orig_ver = settings.corpus_version
    try:
        settings.corpus_version = "curated_kb_v2.0_updated"
        hit2 = SemanticCacheService.lookup(query)
        assert hit2 is None, "Cache should invalidate when corpus version changes"
    finally:
        settings.corpus_version = orig_ver


def test_scenario_12_redis_unavailable_resilience():
    """12. If Redis is unavailable or fails, application continues safely."""
    with patch.object(SemanticCacheService, "get_redis_client", return_value=None):
        hit = SemanticCacheService.lookup("What is migraine?")
        assert hit is None

        stored = SemanticCacheService.store("What is migraine?", "Info", [{"document_id": "MED-01"}])
        assert stored is False

        # SessionService must still work without crashing
        thread_id, reply = SessionService.start_session("Hello")
        assert thread_id
        assert len(reply) > 0


def test_scenario_13_invalid_cached_metadata_or_citation_miss():
    """13. Cached entry with corrupted metadata or empty sources is safely rejected."""
    client = SemanticCacheService.get_redis_client()
    assert client is not None

    # Store malformed entry with empty sources
    key = "blucare:semcache:corrupted_test_key"
    client.hset(key, mapping={
        "query": "what is test",
        "response": "corrupted",
        "sources_json": "[]",  # empty sources
        "vector": b"",  # invalid vector
        "expires_at": str(time.time() + 3600),
        "corpus_version": settings.corpus_version,
        "prompt_version": settings.synthesis_prompt_version,
        "embedding_model": settings.embedding_model_name,
        "generation_model": settings.groq_model,
    })

    hit = SemanticCacheService.lookup("what is test")
    assert hit is None
