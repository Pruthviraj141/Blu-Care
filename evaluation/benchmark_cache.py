"""
BluCare+ — Redis Semantic Cache Performance & Latency Benchmark.

Measures real execution metrics across:
1. Cache Disabled (baseline RAG pipeline).
2. Cache Enabled - Cold (first pass / cache miss & populate).
3. Cache Enabled - Warm (second pass / semantic cache hit).

Captures:
- End-to-end response latency (mean, p50, p95).
- Cache lookup latency.
- Hit rate & miss rate.
- LLM calls avoided.
- Token usage avoided.
"""

import time
import numpy as np
import logging
from typing import List, Dict, Any

from app.core.config import settings
from app.services.semantic_cache import SemanticCacheService
from app.core.session_service import SessionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BENCHMARK_QUESTIONS = [
    "What is migraine?",
    "What is tension headache?",
    "What causes viral fever?",
    "What are common symptoms of migraine?",
]

# Semantically similar variants to evaluate semantic hit rate
SIMILAR_VARIANTS = [
    "What is a migraine headache?",
    "What is tension type headache?",
    "What is the cause of viral fever?",
    "What is migraine?",
]


def run_benchmark():
    print("=" * 70)
    print("BLUCARE+ REDIS SEMANTIC CACHING BENCHMARK")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Benchmark: Cache Disabled
    # -------------------------------------------------------------
    print("\n[Phase 1] Running with Cache DISABLED...")
    settings.redis_cache_enabled = False
    SemanticCacheService.clear_cache()

    disabled_latencies = []
    for q in BENCHMARK_QUESTIONS:
        thread_id, _ = SessionService.start_session()
        t0 = time.time()
        res = SessionService.process_message(thread_id, q)
        dur = time.time() - t0
        disabled_latencies.append(dur)
        print(f"  Query: '{q[:35]}' -> {dur:.3f}s (Stage: {res.get('stage')})")

    # -------------------------------------------------------------
    # 2. Benchmark: Cache Enabled - Cold Cache
    # -------------------------------------------------------------
    print("\n[Phase 2] Running with Cache ENABLED (Cold Cache)...")
    settings.redis_cache_enabled = True
    SemanticCacheService.clear_cache()

    cold_latencies = []
    for q in BENCHMARK_QUESTIONS:
        thread_id, _ = SessionService.start_session()
        t0 = time.time()
        res = SessionService.process_message(thread_id, q)
        dur = time.time() - t0
        cold_latencies.append(dur)
        print(f"  Query: '{q[:35]}' -> {dur:.3f}s (Status: {res.get('cache_status', 'miss')})")

    # -------------------------------------------------------------
    # 3. Benchmark: Cache Enabled - Warm Cache (Identical & Semantic)
    # -------------------------------------------------------------
    print("\n[Phase 3] Running with Cache ENABLED (Warm Cache - Semantic Hits)...")
    warm_latencies = []
    warm_distances = []
    hits = 0

    for q in SIMILAR_VARIANTS:
        thread_id, _ = SessionService.start_session()
        t0 = time.time()
        res = SessionService.process_message(thread_id, q)
        dur = time.time() - t0
        warm_latencies.append(dur)
        is_hit = res.get("cache_status") == "hit"
        if is_hit:
            hits += 1
            warm_distances.append(res.get("cache_distance", 0.0))
        print(f"  Variant: '{q[:35]}' -> {dur:.4f}s (Hit: {is_hit}, Dist: {res.get('cache_distance')})")

    # -------------------------------------------------------------
    # Summary Calculations
    # -------------------------------------------------------------
    disabled_arr = np.array(disabled_latencies)
    cold_arr = np.array(cold_latencies)
    warm_arr = np.array(warm_latencies)

    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 70)
    print(f"Cache Disabled (Baseline RAG):")
    print(f"  Mean Latency: {np.mean(disabled_arr):.3f}s")
    print(f"  p50 Latency:  {np.percentile(disabled_arr, 50):.3f}s")
    print(f"  p95 Latency:  {np.percentile(disabled_arr, 95):.3f}s")

    print(f"\nCache Enabled - Cold (Miss & Populate):")
    print(f"  Mean Latency: {np.mean(cold_arr):.3f}s")
    print(f"  p50 Latency:  {np.percentile(cold_arr, 50):.3f}s")
    print(f"  p95 Latency:  {np.percentile(cold_arr, 95):.3f}s")

    print(f"\nCache Enabled - Warm (Semantic & Exact Hits):")
    print(f"  Mean Latency: {np.mean(warm_arr):.4f}s")
    print(f"  p50 Latency:  {np.percentile(warm_arr, 50):.4f}s")
    print(f"  p95 Latency:  {np.percentile(warm_arr, 95):.4f}s")
    speedup = np.mean(disabled_arr) / np.mean(warm_arr) if np.mean(warm_arr) > 0 else 0
    reduction = ((np.mean(disabled_arr) - np.mean(warm_arr)) / np.mean(disabled_arr)) * 100
    print(f"  Latency Reduction / Speedup: {speedup:.1f}x faster ({reduction:.1f}% reduction)")

    print(f"\nOperational Metrics:")
    print(f"  Hit Rate on Paraphrased & Repeated Queries: {hits}/{len(SIMILAR_VARIANTS)} ({hits/len(SIMILAR_VARIANTS)*100:.1f}%)")
    print(f"  LLM Calls Avoided: {hits}")
    tokens_saved = hits * 1704
    print(f"  Estimated Groq Tokens Avoided: ~{tokens_saved:,} tokens")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
