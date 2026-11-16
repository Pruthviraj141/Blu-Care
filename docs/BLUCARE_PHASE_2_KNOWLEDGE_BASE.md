# BLUCARE+ — PHASE 2 KNOWLEDGE BASE DOCUMENTATION
## Medical Corpus, Provenance & Ingestion Architecture

---

### 1. Document Corpus Overview

The medical knowledge base powers evidence-based triage decision-support for common acute outpatient complaints:
- **Tension-Type Headache (TTH)**
- **Acute Migraine Without Aura**
- **Acute Viral Pharyngitis / Upper Respiratory Infection**
- **Acute Viral Gastroenteritis & Dehydration Prevention**
- **Acute Bronchitis & Cough Assessment**

All knowledge entries originate from peer-reviewed international clinical guidelines:
- **World Health Organization (WHO)** Primary Care Triage Guidelines
- **National Institute for Health and Care Excellence (NICE)** Clinical Guidelines (CG150)
- **Centers for Disease Control and Prevention (CDC)** Clinical Disease References

---

### 2. Document Provenance Contract (`app/rag/provenance.py`)

Every document chunk indexed in Qdrant strictly complies with the `MedicalDocumentMetadata` schema:

| Field | Type | Description |
| :--- | :--- | :--- |
| `document_id` | String | Unique clinical document ID (e.g. `MED-TENSION-HEADACHE-01`) |
| `chunk_id` | String | Deterministic chunk identifier |
| `source_id` | String | Approved publisher ID (e.g. `WHO-PCD`, `NICE-CG`, `CDC-CLINICAL`) |
| `title` | String | Clinical document title |
| `publisher` | String | Publishing medical institution |
| `source_url` | String | Traceable original URL |
| `clinical_topic` | String | Medical category (e.g. `Neurology / Headache`) |
| `content_hash` | String | SHA-256 hash of chunk content |
| `review_status` | Enum | `approved`, `pending_review`, `superseded`, `quarantined` |

---

### 3. Ingestion Pipeline & Storage (`app/rag/document_ingestion.py`)

- **Idempotence**: Deterministic point IDs generated via MD5/SHA256 hashes of chunk IDs guarantee that re-running ingestion does not generate duplicate vector points.
- **Embedding Generation**: Text chunks are embedded into dense 384-dimensional vector spaces using `BAAI/bge-small-en-v1.5` with normalized cosine embeddings.
- **High Availability Storage**: Operates on Qdrant Cloud (`medical_triage_kb`), with an automated local embedded fallback (`qdrant_local_store`) ensuring zero test or development downtime if cloud networks are interrupted.
