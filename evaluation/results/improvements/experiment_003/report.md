# BluCare+ Medical RAG Baseline — Comprehensive Failure Analysis

**Execution Timestamp**: 2026-11-15T06:40:53.300841+00:00  
**Evaluator Model**: `openai/gpt-oss-20b`  
**Embedding Model**: `BAAI/bge-small-en-v1.5`  
**Reranker Model**: `BAAI/bge-reranker-base`  
**Total Cases**: 12 | **Failed Cases**: 6 | **Pass Rate**: 50.0%

## 1. Executive Summary of Baseline Scores

| RAGAS Metric | Measured Score | Clinical Target | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | **0.437** | ≥ 0.80 | ❌ BELOW TARGET |
| **Answer Relevancy** | **0.7096** | ≥ 0.80 | ❌ BELOW TARGET |
| **Context Precision** | **0.8333** | ≥ 0.75 | ✅ PASS |
| **Context Recall** | **0.7917** | ≥ 0.75 | ✅ PASS |

- **Avg Retrieval Latency**: `2.1551s`
- **Avg Generation Latency**: `0.6898s`
- **Total Turn Duration**: `2.845s`

## 2. Performance by Query Category

| Category | Cases | Faithfulness | Relevancy | Context Precision | Context Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ayurvedic_guidance` | 2 | 0.5000 | 0.9492 | 1.0000 | 1.0000 |
| `differential_diagnosis` | 1 | 0.0000 | 0.7526 | 1.0000 | 1.0000 |
| `direct_knowledge` | 3 | 0.6667 | 0.8580 | 1.0000 | 1.0000 |
| `emergency_safety` | 2 | 0.5000 | 0.4842 | 0.5000 | 0.5000 |
| `out_of_corpus` | 1 | 0.0000 | 0.5359 | 0.0000 | 0.0000 |
| `symptom_triage` | 3 | 0.4148 | 0.5952 | 1.0000 | 0.8333 |

## 3. Failure Root Cause Breakdown

| Failure Classification | Incident Count |
| :--- | :---: |
| Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80). | **5** |
| Unsupported generation claim (Faithfulness < 0.80). | **5** |
| Context recall below threshold | **1** |

## 4. Itemized Weak & Failed Test Cases

### Case `TC-TH-02` — Neurology / Headache
- **Query**: *"I have had a tight band around my forehead for 2 days. It feels dull and aching. How should I care for it at home?"*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, AYU-HEADACHE-SHIRASHOOLA-03, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.8000` | Relevancy: `0.5794` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-MIG-01` — Neurology / Migraine
- **Query**: *"What symptoms distinguish acute migraine from ordinary headaches?"*
- **Category**: `direct_knowledge` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-MIGRAINE-WITHOUT-AURA-02`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.7337` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-MIG-02` — Neurology / Migraine
- **Query**: *"I have a throbbing pain on the left side of my head, feeling sick to my stomach, and lights hurt my eyes. What non-drug steps can help?"*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-MIGRAINE-WITHOUT-AURA-02`
- **Retrieved Docs**: `MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.4444` | Relevancy: `0.5928` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-AYU-KASA-01` — Complementary Medicine / Ayurveda
- **Query**: *"What traditional Ayurvedic home remedies are used for throat irritation and cough (Kasa)?"*
- **Category**: `ayurvedic_guidance` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `AYU-RESPIRATORY-KASA-02`
- **Retrieved Docs**: `AYU-RESPIRATORY-KASA-02, AYU-FEVER-JWARA-01, AYU-HEADACHE-SHIRASHOOLA-03`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.9328` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).

### Case `TC-DIFF-01` — Neurology / Headache
- **Query**: *"How do I tell if my headache is a tension headache or a migraine?"*
- **Category**: `differential_diagnosis` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.7526` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-REPH-01` — Neurology / Headache
- **Query**: *"My head feels like it is in a vice grip. No sick feeling, just steady pressure around the temples. Started this morning."*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, AYU-HEADACHE-SHIRASHOOLA-03, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.6134` | Precision: `1.0000` | Recall: `0.5000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).
  - ⚠️ Context recall below threshold: retrieved evidence incomplete relative to reference.
