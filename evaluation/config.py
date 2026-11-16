"""
Configuration for BluCare+ RAGAS Evaluation Framework.
Provides evaluator LLM bindings, embedding configurations, dataset paths,
and evaluation execution parameters.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "datasets" / "medical_rag_golden.json"
COHORT_DATASET_PATH = BASE_DIR / "datasets" / "medical_rag_baseline_cohort.json"
RESULTS_DIR = BASE_DIR / "results"
LATEST_SUMMARY_PATH = RESULTS_DIR / "latest_summary.json"
LATEST_RESULTS_CSV = RESULTS_DIR / "latest_results.csv"
LATEST_FAILURE_ANALYSIS_MD = RESULTS_DIR / "latest_failure_analysis.md"


class EvaluationConfig(BaseModel):
    # Evaluator Model Configuration (Isolated from production generation)
    evaluator_provider: str = os.getenv("EVALUATOR_PROVIDER", "groq")
    evaluator_model: str = os.getenv("EVALUATOR_MODEL", "openai/gpt-oss-20b")
    evaluator_temperature: float = 0.0

    # Production RAG Configuration being Evaluated (Read-Only)
    embedding_model_name: str = settings.embedding_model_name
    reranker_model_name: str = settings.reranker_model_name
    qdrant_collection_name: str = settings.qdrant_collection_name
    score_threshold: float = settings.score_threshold
    fetch_k: int = settings.fetch_k
    final_k: int = settings.final_k

    # Evaluation Batching and Execution Controls
    batch_size: int = 1
    max_retries: int = 5
    retry_delay_seconds: float = 2.5
    timeout_seconds: float = 60.0

    # Metric Thresholds
    faithfulness_threshold: float = 0.80
    answer_relevancy_threshold: float = 0.80
    context_precision_threshold: float = 0.75
    context_recall_threshold: float = 0.75


eval_config = EvaluationConfig()

