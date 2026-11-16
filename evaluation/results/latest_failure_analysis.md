# BluCare+ Medical RAG Baseline — Comprehensive Failure Analysis

**Execution Timestamp**: 2026-11-15T17:15:00.070688+00:00  
**Evaluator Model**: `openai/gpt-oss-20b`  
**Embedding Model**: `BAAI/bge-small-en-v1.5`  
**Reranker Model**: `BAAI/bge-reranker-base`  
**Total Cases**: 1 | **Failed Cases**: 0 | **Pass Rate**: 100.0%

## 1. Executive Summary of Baseline Scores

| RAGAS Metric | Measured Score | Clinical Target | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | **0.95** | ≥ 0.80 | ✅ PASS |
| **Answer Relevancy** | **0.9** | ≥ 0.80 | ✅ PASS |
| **Context Precision** | **1.0** | ≥ 0.75 | ✅ PASS |
| **Context Recall** | **1.0** | ≥ 0.75 | ✅ PASS |

- **Avg Retrieval Latency**: `0.45s`
- **Avg Generation Latency**: `1.2s`
- **Total Turn Duration**: `1.65s`

## 2. Performance by Query Category

| Category | Cases | Faithfulness | Relevancy | Context Precision | Context Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `symptom_triage` | 1 | 0.9500 | 0.9000 | 1.0000 | 1.0000 |

## 3. Failure Root Cause Breakdown

🎉 **Zero failure cases detected! All evaluated queries satisfied required thresholds.**