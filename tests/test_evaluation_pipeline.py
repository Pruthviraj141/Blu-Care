"""
Unit and regression tests for BluCare+ Medical RAGAS Evaluation Framework.
Verifies dataset structure, production adapter integrity, metrics setup,
and report generation.
"""

import pytest
import pandas as pd
from pathlib import Path

from evaluation.config import DATASET_PATH, eval_config
from evaluation.dataset_loader import (
    load_evaluation_dataset,
    MedicalTestCase,
    VALID_DOC_IDS,
)
from evaluation.rag_adapter import ProductionRAGAdapter, RAGExecutionTrace
from evaluation.metrics import MetricsEngine
from evaluation.report import classify_failure, ReportGenerator


def test_dataset_loading_and_validation():
    """Verifies that the golden dataset loads cleanly and adheres to schema."""
    assert DATASET_PATH.exists(), f"Dataset file missing at {DATASET_PATH}"
    cases = load_evaluation_dataset(DATASET_PATH)

    assert len(cases) >= 50, f"Expected at least 50 test cases, found {len(cases)}"

    for tc in cases:
        assert tc.case_id, "Missing case_id"
        assert tc.user_question, f"Missing user_question for {tc.case_id}"
        assert tc.clinical_topic, f"Missing clinical_topic for {tc.case_id}"
        assert tc.reference_answer, f"Missing reference_answer for {tc.case_id}"
        assert tc.case_category in [
            "direct_knowledge",
            "symptom_triage",
            "differential_diagnosis",
            "ayurvedic_guidance",
            "out_of_corpus",
            "insufficient_evidence",
            "emergency_safety",
        ]
        # Validate that all expected document IDs are part of canonical collection
        for doc_id in tc.expected_document_ids:
            assert doc_id in VALID_DOC_IDS, f"Unexpected doc_id '{doc_id}' in case {tc.case_id}"


def test_rag_adapter_execution():
    """Verifies that the production RAG adapter executes live components without error."""
    cases = load_evaluation_dataset(DATASET_PATH)
    sample_case = next(c for c in cases if c.case_id == "TC-TH-01")

    trace = ProductionRAGAdapter.execute_case(sample_case)

    assert isinstance(trace, RAGExecutionTrace)
    assert trace.case_id == "TC-TH-01"
    assert trace.constructed_query, "Constructed query must not be empty"
    assert len(trace.reranked_doc_ids) > 0, "Expected at least 1 retrieved document"
    assert "MED-TENSION-HEADACHE-01" in trace.reranked_doc_ids, "Expected target document retrieved"
    assert trace.generated_answer, "Generated answer must not be empty"
    assert trace.retrieval_duration_s > 0, "Retrieval duration must be positive"
    assert trace.generation_duration_s > 0, "Generation duration must be positive"


def test_metrics_engine_initialization():
    """Verifies that MetricsEngine initializes evaluator LLM and embedding wrappers."""
    engine = MetricsEngine()
    assert len(engine.metrics) == 4
    metric_names = [m.name for m in engine.metrics]
    assert "faithfulness" in metric_names
    assert "answer_relevancy" in metric_names
    assert "context_precision" in metric_names
    assert "context_recall" in metric_names


def test_failure_classification_logic():
    """Verifies root-cause diagnosis rules."""
    # Test case 1: Low faithfulness
    row_faith = pd.Series({
        "faithfulness": 0.40,
        "answer_relevancy": 0.90,
        "context_precision": 0.90,
        "context_recall": 0.90,
        "expected_doc_ids": "MED-TENSION-HEADACHE-01",
        "retrieved_doc_ids": "MED-TENSION-HEADACHE-01",
        "case_category": "direct_knowledge",
        "expected_sufficiency": "sufficient",
        "is_insufficient_evidence": False,
        "citation_valid": True,
        "error": None,
    })
    reasons = classify_failure(row_faith)
    assert any("Faithfulness" in r for r in reasons)

    # Test case 2: Missing target document in retrieval
    row_ret = pd.Series({
        "faithfulness": 0.90,
        "answer_relevancy": 0.90,
        "context_precision": 0.50,
        "context_recall": 0.50,
        "expected_doc_ids": "MED-DENGUE-FEVER-07",
        "retrieved_doc_ids": "MED-TENSION-HEADACHE-01",
        "case_category": "direct_knowledge",
        "expected_sufficiency": "sufficient",
        "is_insufficient_evidence": False,
        "citation_valid": True,
        "error": None,
    })
    reasons_ret = classify_failure(row_ret)
    assert any("retrieval failure" in r.lower() for r in reasons_ret)


def test_report_generation(tmp_path):
    """Verifies summary JSON, CSV, and Markdown generation."""
    sample_df = pd.DataFrame([
        {
            "case_id": "TEST-01",
            "clinical_topic": "Neurology / Headache",
            "case_category": "symptom_triage",
            "expected_sufficiency": "sufficient",
            "faithfulness": 0.95,
            "answer_relevancy": 0.90,
            "context_precision": 1.0,
            "context_recall": 1.0,
            "retrieval_duration_s": 0.45,
            "generation_duration_s": 1.20,
            "retrieved_doc_ids": "MED-TENSION-HEADACHE-01",
            "expected_doc_ids": "MED-TENSION-HEADACHE-01",
            "citation_valid": True,
            "is_insufficient_evidence": False,
            "error": None,
        }
    ])

    summary = ReportGenerator.generate_all(sample_df, experiment_name="test_run", output_dir=tmp_path)
    assert summary["total_cases"] == 1
    assert summary["overall_metrics"]["faithfulness"] == 0.95
    assert summary["overall_metrics"]["context_precision"] == 1.0
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "results.csv").exists()
    assert (tmp_path / "report.md").exists()

