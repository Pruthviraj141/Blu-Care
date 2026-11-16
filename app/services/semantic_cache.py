"""
BluCare+ — Redis-based Semantic Caching Service.

Provides:
- Standalone semantic caching for non-personalized, safe medical educational questions.
- Strict medical bypass rules: active triage, patient symptoms, dosages, and emergencies NEVER use cached responses.
- Reuses existing BGE embedding model (BAAI/bge-small-en-v1.5, 384 dimensions) with zero new model downloads or costs.
- Exact cosine distance comparison calibrated to prevent cross-condition semantic drift.
- Comprehensive metadata validation: invalidates entries on corpus, prompt, or model changes.
- Graceful degradation: never fails or interrupts patient requests if Redis is offline.
"""

import json
import logging
import re
import time
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import redis

from app.core.config import settings
from app.rag.store import embed_query
from app.services.safety_engine import SafetyEngine
from app.services.patient_case import PatientCase

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "blucare:semcache:"

# Regex patterns for deterministic cache eligibility checks
PRONOUN_PATTERN = re.compile(
    r"\b(i|me|my|myself|mine|we|us|our|ours)\b", re.IGNORECASE
)
TEMPORAL_ONSET_PATTERN = re.compile(
    r"\b(for|since|past|started|yesterday|ago|hours?|days?|weeks?|months?)\b", re.IGNORECASE
)
SEVERITY_PATTERN = re.compile(
    r"\b(severe|mild|moderate|unbearable|excruciating|worsening|getting worse|getting better)\b", re.IGNORECASE
)
DOSAGE_MEDICATION_PATTERN = re.compile(
    r"\b(dose|dosage|mg|pill|tablet|capsule|prescribe|prescription|take|taking|paracetamol|ibuprofen|antibiotic|medication|aspirin|tylenol|dosage amount|how much to take)\b",
    re.IGNORECASE,
)
PERSONAL_CONDITION_PATTERN = re.compile(
    r"\b(pregnant|pregnancy|allergy|allergic|diabetic|diabetes|hypertension|surgery|kidney|liver|cardiac|cancer|infant|child|toddler)\b",
    re.IGNORECASE,
)
EDUCATIONAL_INTENT_PATTERN = re.compile(
    r"^(what\s+is|what\s+are|what\s+causes|explain|describe|difference\s+between|tell\s+me\s+about|overview\s+of|definition\s+of|how\s+does|can\s+you\s+explain|give\s+information\s+on)",
    re.IGNORECASE,
)


class SemanticCacheService:
    """Production-grade semantic caching layer for general medical knowledge in BluCare+."""

    _redis_client: Optional[redis.Redis] = None
    _redis_client_init_attempted: bool = False

    @classmethod
    def get_redis_client(cls) -> Optional[redis.Redis]:
        """
        Returns an active Redis client connection.
        Attempts primary REDIS_URL, falling back gracefully to localhost:6379 if hostname is unresolvable.
        Returns None if Redis is completely unreachable.
        """
        if cls._redis_client is not None:
            try:
                cls._redis_client.ping()
                return cls._redis_client
            except Exception:
                cls._redis_client = None

        urls_to_try = [settings.redis_url]
        if "localhost" not in settings.redis_url and "127.0.0.1" not in settings.redis_url:
            urls_to_try.append("redis://localhost:6379/0")

        for url in urls_to_try:
            try:
                client = redis.from_url(
                    url,
                    socket_connect_timeout=1.5,
                    socket_timeout=1.5,
                    decode_responses=False,
                )
                if client.ping():
                    cls._redis_client = client
                    return client
            except Exception as e:
                logger.debug("Could not connect to Redis at %s: %s", url, e)

        return None

    @classmethod
    def is_cache_eligible(
        cls,
        message: str,
        case: Optional[PatientCase] = None,
        turn_id: int = 1,
    ) -> Tuple[bool, str]:
        """
        Strict deterministic eligibility classifier.
        Guarantees that active patient assessments, emergencies, dosages, and personalized triage
        always bypass the semantic cache.
        """
        if not message or not message.strip():
            return False, "empty_query"

        text = message.strip()
        if len(text) < 6:
            return False, "query_too_short"
        if len(text) > 300:
            return False, "query_too_long"

        # 1. Emergency safety check: emergencies must NEVER be cached
        try:
            safety_eval = SafetyEngine.evaluate(text)
            if safety_eval.is_emergency:
                return False, "emergency_safety_trigger"
        except Exception as e:
            logger.debug("Safety evaluation during cache check notice: %s", e)
            return False, "safety_engine_fallback_bypass"

        # 2. Multi-turn conversation dependencies: active dialogue must not replay standalone cache
        if turn_id > 1:
            return False, "active_conversation_turn"

        # 3. Active patient case facts: already recorded symptoms mean an active triage flow
        if case and (case.symptoms or (case.primary_symptom and case.primary_symptom.value)):
            return False, "active_patient_assessment"

        # 4. First-person patient pronouns: indicates personal presentation
        if PRONOUN_PATTERN.search(text):
            return False, "personal_patient_pronouns"

        # 5. Symptom duration or temporal onset: indicates an active episode
        if TEMPORAL_ONSET_PATTERN.search(text):
            return False, "patient_temporal_onset"

        # 6. Severity / quality modifiers: indicates personal symptom description
        if SEVERITY_PATTERN.search(text):
            return False, "patient_severity_qualifier"

        # 7. Medication dosage / prescription requests: must never be served from semantic cache
        if DOSAGE_MEDICATION_PATTERN.search(text):
            return False, "medication_dosage_request"

        # 8. Personal risk factors / health contexts
        if PERSONAL_CONDITION_PATTERN.search(text):
            return False, "personal_condition_context"

        # 9. Verify positive educational intent
        # Standalone educational inquiries (e.g., "What is migraine?", "What is dehydration?")
        if EDUCATIONAL_INTENT_PATTERN.search(text):
            return True, "eligible_general_educational"

        # Safe fallback: if ambiguous, prioritize clinical correctness and bypass
        return False, "ambiguous_intent_safety_bypass"

    @classmethod
    def normalize_query(cls, query: str) -> str:
        """Normalizes query text for consistent embedding comparison."""
        cleaned = re.sub(r"[^\w\s]", " ", query.lower())
        return " ".join(cleaned.split())

    @classmethod
    def lookup(cls, query: str) -> Optional[Dict[str, Any]]:
        """
        Looks up a semantically similar entry in Redis.
        Returns match dict if cosine distance <= threshold and metadata is valid; else None.
        """
        if not settings.redis_cache_enabled:
            return None

        client = cls.get_redis_client()
        if client is None:
            return None

        t0 = time.time()
        norm_query = cls.normalize_query(query)

        try:
            query_vector = np.array(embed_query(norm_query), dtype=np.float32)
            query_norm = np.linalg.norm(query_vector)
            if query_norm == 0:
                return None

            # Retrieve all cache keys
            pattern = f"{CACHE_KEY_PREFIX}*"
            keys = client.keys(pattern)
            if not keys:
                return None

            best_entry = None
            min_distance = float("inf")

            for k in keys:
                raw_data = client.hgetall(k)
                if not raw_data:
                    continue

                # Parse metadata fields
                try:
                    expires_at = float(raw_data.get(b"expires_at", 0))
                    if expires_at <= time.time():
                        client.delete(k)
                        continue

                    # Validate versioning constraints
                    corpus_ver = raw_data.get(b"corpus_version", b"").decode("utf-8")
                    if corpus_ver != settings.corpus_version:
                        continue

                    prompt_ver = raw_data.get(b"prompt_version", b"").decode("utf-8")
                    if prompt_ver != settings.synthesis_prompt_version:
                        continue

                    embed_model = raw_data.get(b"embedding_model", b"").decode("utf-8")
                    if embed_model != settings.embedding_model_name:
                        continue

                    gen_model = raw_data.get(b"generation_model", b"").decode("utf-8")
                    if gen_model != settings.groq_model:
                        continue

                    # Vector comparison
                    vector_bytes = raw_data.get(b"vector")
                    if not vector_bytes:
                        continue

                    cached_vector = np.frombuffer(vector_bytes, dtype=np.float32)
                    cached_norm = np.linalg.norm(cached_vector)
                    if cached_norm == 0:
                        continue

                    # Cosine distance = 1.0 - cosine_similarity
                    cos_sim = float(np.dot(query_vector, cached_vector) / (query_norm * cached_norm))
                    cos_dist = round(1.0 - cos_sim, 4)

                    if cos_dist < min_distance:
                        min_distance = cos_dist
                        best_entry = {
                            "key": k.decode("utf-8") if isinstance(k, bytes) else k,
                            "query": raw_data.get(b"query", b"").decode("utf-8"),
                            "response": raw_data.get(b"response", b"").decode("utf-8"),
                            "sources": json.loads(raw_data.get(b"sources_json", b"[]").decode("utf-8")),
                            "distance": cos_dist,
                            "created_at": float(raw_data.get(b"created_at", 0)),
                        }
                except Exception as parse_err:
                    logger.debug("Failed parsing cache entry %s: %s", k, parse_err)
                    continue

            lookup_duration = round(time.time() - t0, 4)

            # Check threshold constraint
            if best_entry and min_distance <= settings.redis_cache_distance_threshold:
                best_entry["lookup_duration_s"] = lookup_duration
                logger.info(
                    "Semantic cache HIT: query='%s' matched='%s' (distance=%.4f <= %.4f in %.4fs)",
                    query,
                    best_entry["query"],
                    min_distance,
                    settings.redis_cache_distance_threshold,
                    lookup_duration,
                )
                return best_entry

            logger.info(
                "Semantic cache MISS: query='%s' (min_distance=%.4f > threshold=%.4f in %.4fs)",
                query,
                min_distance,
                settings.redis_cache_distance_threshold,
                lookup_duration,
            )
            return None

        except Exception as e:
            logger.warning("Redis semantic cache lookup error (%s). Proceeding without cache.", e)
            return None

    @classmethod
    def store(
        cls,
        query: str,
        response: str,
        sources: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Stores an eligible educational RAG response in Redis with full metadata and TTL.
        Returns True if successfully stored, False otherwise.
        """
        if not settings.redis_cache_enabled:
            return False

        if not query or not response or not sources:
            return False

        client = cls.get_redis_client()
        if client is None:
            return False

        t0 = time.time()
        norm_query = cls.normalize_query(query)

        try:
            vector = np.array(embed_query(norm_query), dtype=np.float32)
            vector_bytes = vector.tobytes()

            import hashlib
            query_hash = hashlib.sha256(norm_query.encode("utf-8")).hexdigest()[:16]
            cache_key = f"{CACHE_KEY_PREFIX}{query_hash}"

            now = time.time()
            ttl = settings.redis_cache_ttl_seconds
            expires_at = now + ttl

            # Prepare sanitized sources list
            clean_sources = []
            for s in sources:
                if isinstance(s, dict):
                    clean_sources.append({
                        "document_id": s.get("document_id") or s.get("id"),
                        "title": s.get("title", ""),
                        "publisher": s.get("publisher", ""),
                        "ref_id": s.get("ref_id", ""),
                    })

            entry_data = {
                "query": norm_query,
                "response": response,
                "sources_json": json.dumps(clean_sources),
                "vector": vector_bytes,
                "embedding_model": settings.embedding_model_name,
                "generation_model": settings.groq_model,
                "prompt_version": settings.synthesis_prompt_version,
                "corpus_version": settings.corpus_version,
                "category": "general_educational",
                "created_at": str(now),
                "expires_at": str(expires_at),
            }

            client.hset(cache_key, mapping=entry_data)
            client.expire(cache_key, ttl)

            store_duration = round(time.time() - t0, 4)
            logger.info("Stored semantic cache entry for '%s' (TTL=%ds in %.4fs)", query, ttl, store_duration)
            return True

        except Exception as e:
            logger.warning("Failed to store entry in Redis semantic cache: %s", e)
            return False

    @classmethod
    def clear_cache(cls) -> int:
        """Flushes all BluCare semantic cache entries. Returns count of deleted keys."""
        client = cls.get_redis_client()
        if not client:
            return 0
        try:
            keys = client.keys(f"{CACHE_KEY_PREFIX}*")
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning("Error clearing cache: %s", e)
            return 0

