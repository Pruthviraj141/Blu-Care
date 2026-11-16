# BluCare+ Medical RAG Baseline — Comprehensive Failure Analysis

**Execution Timestamp**: 2026-11-15T17:07:57.748322+00:00  
**Evaluator Model**: `openai/gpt-oss-20b`  
**Embedding Model**: `BAAI/bge-small-en-v1.5`  
**Reranker Model**: `BAAI/bge-reranker-base`  
**Total Cases**: 12 | **Failed Cases**: 4 | **Pass Rate**: 66.7%

## 1. Executive Summary of Baseline Scores

| RAGAS Metric | Measured Score | Clinical Target | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | **0.7038** | ≥ 0.80 | ❌ BELOW TARGET |
| **Answer Relevancy** | **0.8046** | ≥ 0.80 | ✅ PASS |
| **Context Precision** | **0.9028** | ≥ 0.75 | ✅ PASS |
| **Context Recall** | **0.8472** | ≥ 0.75 | ✅ PASS |

- **Avg Retrieval Latency**: `0.856s`
- **Avg Generation Latency**: `1.7977s`
- **Total Turn Duration**: `2.6537s`

## 2. Performance by Query Category

| Category | Cases | Faithfulness | Relevancy | Context Precision | Context Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ayurvedic_guidance` | 2 | 1.0000 | 0.9499 | 1.0000 | 1.0000 |
| `differential_diagnosis` | 1 | 0.9286 | 0.8505 | 1.0000 | 1.0000 |
| `direct_knowledge` | 3 | 0.9444 | 0.9226 | 1.0000 | 1.0000 |
| `emergency_safety` | 2 | 0.2500 | 0.8933 | 0.9167 | 0.8333 |
| `out_of_corpus` | 1 | 0.0000 | 0.5359 | 0.0000 | 0.0000 |
| `symptom_triage` | 3 | 0.7278 | 0.6049 | 1.0000 | 0.8333 |

## 3. Failure Root Cause Breakdown

| Failure Classification | Incident Count |
| :--- | :---: |
| Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80). | **3** |
| Unsupported generation claim (Faithfulness < 0.80). | **3** |
| Context recall below threshold | **1** |

## 4. Itemized Weak & Failed Test Cases

### Case `TC-TH-02` — Neurology / Headache
- **Query**: *"I have had a tight band around my forehead for 2 days. It feels dull and aching. How should I care for it at home?"*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, AYU-HEADACHE-SHIRASHOOLA-03, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.8333` | Relevancy: `0.5953` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-MIG-02` — Neurology / Migraine
- **Query**: *"I have a throbbing pain on the left side of my head, feeling sick to my stomach, and lights hurt my eyes. What non-drug steps can help?"*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-MIGRAINE-WITHOUT-AURA-02`
- **Retrieved Docs**: `MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.6000` | Relevancy: `0.5928` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-URI-03` — Infectious Disease / Respiratory
- **Query**: *"What red-flag signs mean a sore throat is dangerous and requires emergency medical care?"*
- **Category**: `emergency_safety` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-VIRAL-PHARYNGITIS-03`
- **Retrieved Docs**: `MED-VIRAL-PHARYNGITIS-03, MED-INFLUENZA-08, MED-VIRAL-FEVER-06, MED-ACUTE-GASTROENTERITIS-04`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.9612` | Precision: `0.8333` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).

### Case `TC-REPH-01` — Neurology / Headache
- **Query**: *"My head feels like it is in a vice grip. No sick feeling, just steady pressure around the temples. Started this morning."*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, AYU-HEADACHE-SHIRASHOOLA-03, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.7500` | Relevancy: `0.6265` | Precision: `1.0000` | Recall: `0.5000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).
  - ⚠️ Context recall below threshold: retrieved evidence incomplete relative to reference.
