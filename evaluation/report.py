"""
Reporting and Failure Analysis Generator for BluCare+ Medical RAG Evaluation.
Produces:
1. latest_summary.json (Machine-readable overall & grouped metrics)
2. latest_results.csv (Per-case results and latencies)
3. latest_failure_analysis.md (Root-cause classification of weak cases)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from evaluation.config import (
    eval_config,
    LATEST_SUMMARY_PATH,
    LATEST_RESULTS_CSV,
    LATEST_FAILURE_ANALYSIS_MD,
)

logger = logging.getLogger(__name__)


def classify_failure(row: pd.Series) -> List[str]:
    """Classifies root causes for test cases failing evaluation thresholds."""
    reasons = []

    faithfulness = row.get("faithfulness", 0.0)
    answer_relevancy = row.get("answer_relevancy", 0.0)
    context_precision = row.get("context_precision", 0.0)
    context_recall = row.get("context_recall", 0.0)
    expected_doc_ids = [d.strip() for d in str(row.get("expected_doc_ids", "")).split(",") if d.strip()]
    retrieved_doc_ids = [d.strip() for d in str(row.get("retrieved_doc_ids", "")).split(",") if d.strip()]
    category = row.get("case_category", "")
    expected_sufficiency = row.get("expected_sufficiency", "sufficient")
    is_insufficient = row.get("is_insufficient_evidence", False)
    error = row.get("error")

    if pd.isna(faithfulness):
        faithfulness = 0.0
    if pd.isna(answer_relevancy):
        answer_relevancy = 0.0
    if pd.isna(context_precision):
        context_precision = 0.0
    if pd.isna(context_recall):
        context_recall = 0.0

    if error:
        reasons.append(f"Execution Error: {error}")
        return reasons

    # Out of corpus & Emergency safety abstention cases
    if category == "out_of_corpus" or expected_sufficiency == "insufficient":
        if not is_insufficient and len(retrieved_doc_ids) > 0:
            reasons.append("Incorrect abstention: retrieved irrelevant documents for out-of-corpus query.")
        else:
            return []  # Successfully recognized missing evidence

    if expected_sufficiency == "emergency_abstention":
        if not is_insufficient:
            reasons.append("Emergency safety failure: failed to escalate emergency presentation.")
        else:
            return []  # Successfully escalated emergency presentation

    # Retrieval coverage checks
    if expected_doc_ids:
        missing_docs = [d for d in expected_doc_ids if d not in retrieved_doc_ids]
        if missing_docs and len(missing_docs) == len(expected_doc_ids):
            reasons.append(f"Embedding or retrieval failure: missing target documents {missing_docs}.")
        elif missing_docs:
            reasons.append(f"Partial retrieval coverage: found only {retrieved_doc_ids}, missed {missing_docs}.")

    # Ranking checks
    if context_precision < eval_config.context_precision_threshold and len(retrieved_doc_ids) > 1:
        if expected_doc_ids and retrieved_doc_ids and retrieved_doc_ids[0] not in expected_doc_ids:
            reasons.append(
                f"CrossEncoder ranking failure: top ranked document '{retrieved_doc_ids[0]}' is not the primary expected target."
            )
        else:
            reasons.append("Context precision below threshold (relevant documents ranked too low).")

    # Generation checks
    if faithfulness < eval_config.faithfulness_threshold:
        reasons.append("Unsupported generation claim (Faithfulness < 0.80).")

    if answer_relevancy < eval_config.answer_relevancy_threshold:
        reasons.append("Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).")

    if context_recall < eval_config.context_recall_threshold and expected_sufficiency == "sufficient":
        reasons.append("Context recall below threshold: retrieved evidence incomplete relative to reference.")

    if not row.get("citation_valid", True):
        reasons.append("Citation validation failure: generated citation not present in retrieved context.")

    return reasons


class ReportGenerator:
    """Computes summary statistics and exports JSON, CSV, and Markdown analysis."""

    @classmethod
    def generate_all(
        cls,
        df: pd.DataFrame,
        experiment_name: str = "baseline_run",
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        target_dir = output_dir or LATEST_SUMMARY_PATH.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Clean NaN values for metrics
        metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
        for col in metric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0.0)

        # 2. Compute Overall Summary
        total_cases = len(df)
        avg_faithfulness = float(df["faithfulness"].mean()) if total_cases > 0 else 0.0
        avg_answer_relevancy = float(df["answer_relevancy"].mean()) if total_cases > 0 else 0.0
        avg_context_precision = float(df["context_precision"].mean()) if total_cases > 0 else 0.0
        avg_context_recall = float(df["context_recall"].mean()) if total_cases > 0 else 0.0
        avg_retrieval_lat = float(df["retrieval_duration_s"].mean()) if total_cases > 0 else 0.0
        avg_gen_lat = float(df["generation_duration_s"].mean()) if total_cases > 0 else 0.0

        # Group by Category
        category_metrics = {}
        for cat, group in df.groupby("case_category"):
            category_metrics[cat] = {
                "count": len(group),
                "faithfulness": round(float(group["faithfulness"].mean()), 4),
                "answer_relevancy": round(float(group["answer_relevancy"].mean()), 4),
                "context_precision": round(float(group["context_precision"].mean()), 4),
                "context_recall": round(float(group["context_recall"].mean()), 4),
                "avg_retrieval_s": round(float(group["retrieval_duration_s"].mean()), 4),
                "avg_generation_s": round(float(group["generation_duration_s"].mean()), 4),
            }

        # Group by Clinical Topic
        topic_metrics = {}
        for topic, group in df.groupby("clinical_topic"):
            topic_metrics[topic] = {
                "count": len(group),
                "faithfulness": round(float(group["faithfulness"].mean()), 4),
                "answer_relevancy": round(float(group["answer_relevancy"].mean()), 4),
                "context_precision": round(float(group["context_precision"].mean()), 4),
                "context_recall": round(float(group["context_recall"].mean()), 4),
            }

        # 3. Diagnose Failures
        df["failure_reasons"] = df.apply(classify_failure, axis=1)
        df["is_failure"] = df["failure_reasons"].apply(lambda r: len(r) > 0)
        failed_df = df[df["is_failure"]]

        summary = {
            "experiment": experiment_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_cases": total_cases,
            "failed_cases_count": len(failed_df),
            "pass_rate": round((total_cases - len(failed_df)) / total_cases, 4) if total_cases > 0 else 0.0,
            "overall_metrics": {
                "faithfulness": round(avg_faithfulness, 4),
                "answer_relevancy": round(avg_answer_relevancy, 4),
                "context_precision": round(avg_context_precision, 4),
                "context_recall": round(avg_context_recall, 4),
            },
            "latency": {
                "avg_retrieval_duration_s": round(avg_retrieval_lat, 4),
                "avg_generation_duration_s": round(avg_gen_lat, 4),
                "total_avg_turn_s": round(avg_retrieval_lat + avg_gen_lat, 4),
            },
            "configuration": {
                "evaluator_model": eval_config.evaluator_model,
                "evaluator_provider": eval_config.evaluator_provider,
                "embedding_model": eval_config.embedding_model_name,
                "reranker_model": eval_config.reranker_model_name,
                "qdrant_collection": eval_config.qdrant_collection_name,
                "score_threshold": eval_config.score_threshold,
                "fetch_k": eval_config.fetch_k,
                "final_k": eval_config.final_k,
            },
            "category_metrics": category_metrics,
            "topic_metrics": topic_metrics,
        }

        # 4. Save JSON Summary
        summary_path = (target_dir / "summary.json") if output_dir else LATEST_SUMMARY_PATH
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info("Saved evaluation summary to %s", summary_path)

        # 5. Save Results CSV
        results_csv_path = (target_dir / "results.csv") if output_dir else LATEST_RESULTS_CSV
        export_df = df.copy()
        export_df["failure_reasons"] = export_df["failure_reasons"].apply(lambda r: " | ".join(r) if isinstance(r, list) else str(r))
        export_df.to_csv(results_csv_path, index=False)
        logger.info("Saved detailed results CSV to %s", results_csv_path)

        # 6. Generate Markdown Failure Analysis
        md_content = cls._build_failure_analysis_markdown(summary, failed_df, df)
        report_md_path = (target_dir / "report.md") if output_dir else LATEST_FAILURE_ANALYSIS_MD
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Saved failure analysis to %s", report_md_path)

        # Also write latest copy if output_dir was set
        if output_dir:
            with open(LATEST_SUMMARY_PATH, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            export_df.to_csv(LATEST_RESULTS_CSV, index=False)
            with open(LATEST_FAILURE_ANALYSIS_MD, "w", encoding="utf-8") as f:
                f.write(md_content)

        return summary

    @classmethod
    def _build_failure_analysis_markdown(
        cls,
        summary: Dict[str, Any],
        failed_df: pd.DataFrame,
        all_df: pd.DataFrame,
    ) -> str:
        lines = [
            "# BluCare+ Medical RAG Baseline — Comprehensive Failure Analysis",
            "",
            f"**Execution Timestamp**: {summary['timestamp']}  ",
            f"**Evaluator Model**: `{summary['configuration']['evaluator_model']}`  ",
            f"**Embedding Model**: `{summary['configuration']['embedding_model']}`  ",
            f"**Reranker Model**: `{summary['configuration']['reranker_model']}`  ",
            f"**Total Cases**: {summary['total_cases']} | **Failed Cases**: {summary['failed_cases_count']} | **Pass Rate**: {summary['pass_rate'] * 100:.1f}%",
            "",
            "## 1. Executive Summary of Baseline Scores",
            "",
            "| RAGAS Metric | Measured Score | Clinical Target | Status |",
            "| :--- | :---: | :---: | :---: |",
            f"| **Faithfulness** | **{summary['overall_metrics']['faithfulness']}** | ≥ 0.80 | {'✅ PASS' if summary['overall_metrics']['faithfulness'] >= 0.80 else '❌ BELOW TARGET'} |",
            f"| **Answer Relevancy** | **{summary['overall_metrics']['answer_relevancy']}** | ≥ 0.80 | {'✅ PASS' if summary['overall_metrics']['answer_relevancy'] >= 0.80 else '❌ BELOW TARGET'} |",
            f"| **Context Precision** | **{summary['overall_metrics']['context_precision']}** | ≥ 0.75 | {'✅ PASS' if summary['overall_metrics']['context_precision'] >= 0.75 else '❌ BELOW TARGET'} |",
            f"| **Context Recall** | **{summary['overall_metrics']['context_recall']}** | ≥ 0.75 | {'✅ PASS' if summary['overall_metrics']['context_recall'] >= 0.75 else '❌ BELOW TARGET'} |",
            "",
            f"- **Avg Retrieval Latency**: `{summary['latency']['avg_retrieval_duration_s']}s`",
            f"- **Avg Generation Latency**: `{summary['latency']['avg_generation_duration_s']}s`",
            f"- **Total Turn Duration**: `{summary['latency']['total_avg_turn_s']}s`",
            "",
            "## 2. Performance by Query Category",
            "",
            "| Category | Cases | Faithfulness | Relevancy | Context Precision | Context Recall |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        for cat, m in summary["category_metrics"].items():
            lines.append(
                f"| `{cat}` | {m['count']} | {m['faithfulness']:.4f} | {m['answer_relevancy']:.4f} | {m['context_precision']:.4f} | {m['context_recall']:.4f} |"
            )

        lines.extend([
            "",
            "## 3. Failure Root Cause Breakdown",
            "",
        ])

        if len(failed_df) == 0:
            lines.append("🎉 **Zero failure cases detected! All evaluated queries satisfied required thresholds.**")
        else:
            # Aggregate failure causes
            cause_counts = {}
            for causes in failed_df["failure_reasons"]:
                for c in causes:
                    prefix = c.split(":")[0]
                    cause_counts[prefix] = cause_counts.get(prefix, 0) + 1

            lines.append("| Failure Classification | Incident Count |")
            lines.append("| :--- | :---: |")
            for cause, cnt in sorted(cause_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {cause} | **{cnt}** |")

            lines.extend([
                "",
                "## 4. Itemized Weak & Failed Test Cases",
                "",
            ])

            for _, row in failed_df.iterrows():
                lines.extend([
                    f"### Case `{row['case_id']}` — {row['clinical_topic']}",
                    f"- **Query**: *\"{row.get('user_input', '')}\"*",
                    f"- **Category**: `{row.get('case_category')}` | **Sufficiency Target**: `{row.get('expected_sufficiency')}`",
                    f"- **Expected Docs**: `{row.get('expected_doc_ids')}`",
                    f"- **Retrieved Docs**: `{row.get('retrieved_doc_ids')}`",
                    f"- **Scores**: Faithfulness: `{row.get('faithfulness'):.4f}` | Relevancy: `{row.get('answer_relevancy'):.4f}` | Precision: `{row.get('context_precision'):.4f}` | Recall: `{row.get('context_recall'):.4f}`",
                    f"- **Root Cause Diagnoses**:",
                ])
                for r in row["failure_reasons"]:
                    lines.append(f"  - ⚠️ {r}")
                lines.append("")

        return "\n".join(lines)
