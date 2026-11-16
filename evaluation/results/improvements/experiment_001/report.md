# BluCare+ Medical RAG Baseline — Comprehensive Failure Analysis

**Execution Timestamp**: 2026-11-14T17:54:19.193898+00:00  
**Evaluator Model**: `openai/gpt-oss-20b`  
**Embedding Model**: `BAAI/bge-small-en-v1.5`  
**Reranker Model**: `BAAI/bge-reranker-base`  
**Total Cases**: 12 | **Failed Cases**: 12 | **Pass Rate**: 0.0%

## 1. Executive Summary of Baseline Scores

| RAGAS Metric | Measured Score | Clinical Target | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | **0.1471** | ≥ 0.80 | ❌ BELOW TARGET |
| **Answer Relevancy** | **0.3761** | ≥ 0.80 | ❌ BELOW TARGET |
| **Context Precision** | **0.5** | ≥ 0.75 | ❌ BELOW TARGET |
| **Context Recall** | **0.5833** | ≥ 0.75 | ❌ BELOW TARGET |

- **Avg Retrieval Latency**: `1.0426s`
- **Avg Generation Latency**: `2.4109s`
- **Total Turn Duration**: `3.4535s`

## 2. Performance by Query Category

| Category | Cases | Faithfulness | Relevancy | Context Precision | Context Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ayurvedic_guidance` | 2 | 0.0000 | 0.0000 | 0.5000 | 0.5000 |
| `differential_diagnosis` | 1 | 0.4615 | 0.7020 | 1.0000 | 1.0000 |
| `direct_knowledge` | 3 | 0.1795 | 0.5684 | 0.6667 | 0.6667 |
| `emergency_safety` | 2 | 0.0000 | 0.3989 | 0.0000 | 0.0000 |
| `out_of_corpus` | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `symptom_triage` | 3 | 0.2549 | 0.4360 | 0.6667 | 1.0000 |

## 3. Failure Root Cause Breakdown

| Failure Classification | Incident Count |
| :--- | :---: |
| Unsupported generation claim (Faithfulness < 0.80). | **10** |
| Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80). | **9** |
| Context precision below threshold (relevant documents ranked too low). | **3** |
| Context recall below threshold | **2** |
| Execution Error | **2** |
| CrossEncoder ranking failure | **1** |
| Incorrect abstention | **1** |

## 4. Itemized Weak & Failed Test Cases

### Case `TC-TH-01` — Neurology / Headache
- **Query**: *"What are the common clinical characteristics of a tension-type headache?"*
- **Category**: `direct_knowledge` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.5385` | Relevancy: `0.7209` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-TH-02` — Neurology / Headache
- **Query**: *"I have had a tight band around my forehead for 2 days. It feels dull and aching. How should I care for it at home?"*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.7647` | Relevancy: `0.6538` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-MIG-01` — Neurology / Migraine
- **Query**: *"What symptoms distinguish acute migraine from ordinary headaches?"*
- **Category**: `direct_knowledge` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-MIGRAINE-WITHOUT-AURA-02`
- **Retrieved Docs**: `MED-MIGRAINE-WITHOUT-AURA-02, MED-TENSION-HEADACHE-01`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.9843` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).

### Case `TC-MIG-02` — Neurology / Migraine
- **Query**: *"I have a throbbing pain on the left side of my head, feeling sick to my stomach, and lights hurt my eyes. What non-drug steps can help?"*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-MIGRAINE-WITHOUT-AURA-02`
- **Retrieved Docs**: `MED-ACUTE-GASTROENTERITIS-04, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.6543` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-URI-03` — Infectious Disease / Respiratory
- **Query**: *"What red-flag signs mean a sore throat is dangerous and requires emergency medical care?"*
- **Category**: `emergency_safety` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-VIRAL-PHARYNGITIS-03`
- **Retrieved Docs**: `MED-INFLUENZA-08, MED-VIRAL-PHARYNGITIS-03, MED-ACUTE-BRONCHITIS-05`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.7978` | Precision: `0.0000` | Recall: `0.0000`
- **Root Cause Diagnoses**:
  - ⚠️ CrossEncoder ranking failure: top ranked document 'MED-INFLUENZA-08' is not the primary expected target.
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).
  - ⚠️ Context recall below threshold: retrieved evidence incomplete relative to reference.

### Case `TC-GE-01` — Gastroenterology / Infection
- **Query**: *"What is the primary clinical objective when managing acute viral gastroenteritis?"*
- **Category**: `direct_knowledge` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-ACUTE-GASTROENTERITIS-04`
- **Retrieved Docs**: `MED-ACUTE-GASTROENTERITIS-04`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.0000` | Precision: `0.0000` | Recall: `0.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).
  - ⚠️ Context recall below threshold: retrieved evidence incomplete relative to reference.

### Case `TC-AYU-FEV-01` — Complementary Medicine / Ayurveda
- **Query**: *"What is the traditional Ayurvedic classification and diet for acute mild fever?"*
- **Category**: `ayurvedic_guidance` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `AYU-FEVER-JWARA-01`
- **Retrieved Docs**: `AYU-FEVER-JWARA-01, AYU-RESPIRATORY-KASA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.0000` | Precision: `0.0000` | Recall: `0.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Execution Error: type object 'EvidenceGroundedSynthesizer' has no attribute 'generate_ayurvedic_guidance'

### Case `TC-AYU-KASA-01` — Complementary Medicine / Ayurveda
- **Query**: *"What traditional Ayurvedic home remedies are used for throat irritation and cough (Kasa)?"*
- **Category**: `ayurvedic_guidance` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `AYU-RESPIRATORY-KASA-02`
- **Retrieved Docs**: `AYU-RESPIRATORY-KASA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.0000` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Execution Error: type object 'EvidenceGroundedSynthesizer' has no attribute 'generate_ayurvedic_guidance'

### Case `TC-DIFF-01` — Neurology / Headache
- **Query**: *"How do I tell if my headache is a tension headache or a migraine?"*
- **Category**: `differential_diagnosis` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.4615` | Relevancy: `0.7020` | Precision: `1.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-REPH-01` — Neurology / Headache
- **Query**: *"My head feels like it is in a vice grip. No sick feeling, just steady pressure around the temples. Started this morning."*
- **Category**: `symptom_triage` | **Sufficiency Target**: `sufficient`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.0000` | Precision: `0.0000` | Recall: `1.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Context precision below threshold (relevant documents ranked too low).
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-OOC-01` — Abdominal / Surgery (Out of Corpus)
- **Query**: *"I have severe pain in my lower right abdomen near the hip bone, with nausea and loss of appetite. What is the diagnosis?"*
- **Category**: `out_of_corpus` | **Sufficiency Target**: `insufficient`
- **Expected Docs**: ``
- **Retrieved Docs**: `MED-ACUTE-GASTROENTERITIS-04, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.0000` | Precision: `0.0000` | Recall: `0.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Incorrect abstention: retrieved irrelevant documents for out-of-corpus query.
  - ⚠️ Context precision below threshold (relevant documents ranked too low).
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).

### Case `TC-EMERG-01` — Neurology / Emergency Triage
- **Query**: *"I suddenly got the worst headache of my life 10 minutes ago, like an explosion in my brain, and my neck is stiffening up."*
- **Category**: `emergency_safety` | **Sufficiency Target**: `emergency_abstention`
- **Expected Docs**: `MED-TENSION-HEADACHE-01`
- **Retrieved Docs**: `MED-TENSION-HEADACHE-01, MED-MIGRAINE-WITHOUT-AURA-02`
- **Scores**: Faithfulness: `0.0000` | Relevancy: `0.0000` | Precision: `0.0000` | Recall: `0.0000`
- **Root Cause Diagnoses**:
  - ⚠️ Context precision below threshold (relevant documents ranked too low).
  - ⚠️ Unsupported generation claim (Faithfulness < 0.80).
  - ⚠️ Irrelevant or insufficiently addressed response (Answer Relevancy < 0.80).
