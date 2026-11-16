"""
Evaluation Runner for BluCare+ Medical RAG Benchmark.
Executes batch evaluation, handles rate limits, preserves partial results,
and outputs standardized reports.
"""

import sys
import time
import argparse
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd

from evaluation.config import eval_config, DATASET_PATH
from evaluation.dataset_loader import load_evaluation_dataset, MedicalTestCase
from evaluation.rag_adapter import ProductionRAGAdapter, RAGExecutionTrace
from evaluation.metrics import MetricsEngine
from evaluation.report import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("evaluation.runner")


def run_evaluation(
    dataset_path: Path = DATASET_PATH,
    limit: Optional[int] = None,
    batch_size: int = 1,
    experiment_name: str = "blucare_improved_v2",
    output_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Executes the full evaluation lifecycle."""
    logger.info("Starting BluCare+ RAGAS Evaluation: %s", experiment_name)
    logger.info("Loading dataset from: %s", dataset_path)

    cases: List[MedicalTestCase] = load_evaluation_dataset(dataset_path)
    if limit and limit > 0:
        logger.info("Limiting evaluation to first %d of %d cases", limit, len(cases))
        cases = cases[:limit]

    total_cases = len(cases)
    logger.info("Total test cases to evaluate: %d (Batch size: %d)", total_cases, batch_size)

    metrics_engine = MetricsEngine()
    batch_dfs: List[pd.DataFrame] = []

    # Process in batches
    for i in range(0, total_cases, batch_size):
        batch_cases = cases[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_cases + batch_size - 1) // batch_size
        logger.info("--- Processing Batch %d/%d (%d cases) ---", batch_num, total_batches, len(batch_cases))

        # 1. Execute live production RAG pipeline for batch cases
        batch_traces: List[RAGExecutionTrace] = []
        for tc in batch_cases:
            logger.info("Executing production RAG for case: %s ('%s')", tc.case_id, tc.user_question[:45])
            trace = ProductionRAGAdapter.execute_case(tc)
            batch_traces.append(trace)
            time.sleep(0.5)  # Polite pacing between generation turns

        # 2. Evaluate batch with RAGAS metrics
        logger.info("Evaluating RAGAS metrics for Batch %d...", batch_num)
        batch_df = metrics_engine.evaluate_batch(batch_traces, batch_cases)
        batch_dfs.append(batch_df)

        # 3. Inter-batch delay to respect Groq rate limits
        if i + batch_size < total_cases:
            logger.info("Pacing delay: sleeping %.1fs before next batch...", eval_config.retry_delay_seconds)
            time.sleep(eval_config.retry_delay_seconds)

    # 4. Aggregate full results
    full_df = pd.concat(batch_dfs, ignore_index=True) if batch_dfs else pd.DataFrame()
    logger.info("Completed execution across %d cases.", len(full_df))

    # 5. Generate comprehensive reports (JSON, CSV, Markdown)
    summary = ReportGenerator.generate_all(full_df, experiment_name=experiment_name, output_dir=output_dir)

    # 6. Display Console Summary Table
    print("\n" + "=" * 70)
    print(f" BLUCARE+ MEDICAL RAGAS EVALUATION RESULTS — {experiment_name.upper()}")
    print("=" * 70)
    print(f"Evaluator Model   : {summary['configuration']['evaluator_model']}")
    print(f"Total Test Cases  : {summary['total_cases']}")
    print(f"Failed Cases      : {summary['failed_cases_count']} ({summary['pass_rate'] * 100:.1f}% pass rate)")
    print("-" * 70)
    m = summary["overall_metrics"]
    print(f"Faithfulness      : {m['faithfulness']:.4f} (Target ≥ 0.80) -> {'PASS' if m['faithfulness'] >= 0.80 else 'FAIL'}")
    print(f"Answer Relevancy  : {m['answer_relevancy']:.4f} (Target ≥ 0.80) -> {'PASS' if m['answer_relevancy'] >= 0.80 else 'FAIL'}")
    print(f"Context Precision : {m['context_precision']:.4f} (Target ≥ 0.75) -> {'PASS' if m['context_precision'] >= 0.75 else 'FAIL'}")
    print(f"Context Recall    : {m['context_recall']:.4f} (Target ≥ 0.75) -> {'PASS' if m['context_recall'] >= 0.75 else 'FAIL'}")
    print("-" * 70)
    lat = summary["latency"]
    print(f"Avg Retrieval Latency : {lat['avg_retrieval_duration_s']}s")
    print(f"Avg Generation Latency: {lat['avg_generation_duration_s']}s")
    print(f"Total Avg Turn Latency: {lat['total_avg_turn_s']}s")
    print("=" * 70 + "\n")

    return full_df


def main():
    parser = argparse.ArgumentParser(description="BluCare+ Medical RAGAS Evaluation Runner")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases to evaluate")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for RAGAS evaluation")
    parser.add_argument("--experiment-name", type=str, default="blucare_improved_v2", help="Experiment name tag")
    parser.add_argument("--dataset", type=str, default=str(DATASET_PATH), help="Path to golden dataset JSON")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save experiment results")
    parser.add_argument("--evaluator-model", type=str, default=None, help="Evaluator model override")
    args = parser.parse_args()

    if args.evaluator_model:
        eval_config.evaluator_model = args.evaluator_model

    run_evaluation(
        dataset_path=Path(args.dataset),
        limit=args.limit,
        batch_size=args.batch_size,
        experiment_name=args.experiment_name,
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )


if __name__ == "__main__":
    main()

