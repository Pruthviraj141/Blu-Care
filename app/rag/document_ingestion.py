import logging
import hashlib
from typing import List, Dict, Any, Optional
from qdrant_client import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.rag.store import get_qdrant_client, get_embeddings
from app.rag.provenance import MedicalDocumentMetadata, DocumentReviewStatus

logger = logging.getLogger(__name__)


CURATED_MEDICAL_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "document_id": "MED-TENSION-HEADACHE-01",
        "title": "Tension-Type Headache Clinical Diagnosis & Home Care",
        "publisher": "WHO Primary Care Triage Guidelines",
        "source_url": "https://www.who.int/publications/i/item/tension-headache-guidelines",
        "clinical_topic": "Neurology / Headache",
        "content": (
            "Tension-type headache (TTH) is characterized by dull, non-throbbing, band-like pain around the head or neck. "
            "Severity is typically mild to moderate (scale 2-6/10) lasting from hours to several days. "
            "Unlike migraine, it lacks systemic features like severe vomiting, focal neurological signs, or photophobia with aura. "
            "Evidence-based supportive care includes adequate hydration, rest in a quiet environment, neck muscle relaxation, "
            "and avoidance of prolonged screen exposure. Warning signs requiring physician evaluation include sudden thunderclap onset, "
            "fever with neck stiffness, or headache following head trauma."
        ),
    },
    {
        "document_id": "MED-MIGRAINE-WITHOUT-AURA-02",
        "title": "Clinical Diagnosis and Management of Acute Migraine",
        "publisher": "NICE Clinical Guidelines (CG150)",
        "source_url": "https://www.nice.org.uk/guidance/cg150",
        "clinical_topic": "Neurology / Migraine",
        "content": (
            "Migraine is a recurrent neurological disorder typically presenting with unilateral, throbbing or pulsating moderate-to-severe "
            "headache lasting 4 to 72 hours. It is frequently accompanied by nausea, vomiting, photophobia, or phonophobia. "
            "First-line self-care: rest in a quiet, dark room, adequate fluid intake, cold compress applied to the forehead or neck. "
            "Patients should seek urgent medical care if experiencing hemiplegia, confusion, speech difficulties, or visual loss."
        ),
    },
    {
        "document_id": "MED-VIRAL-PHARYNGITIS-03",
        "title": "Acute Upper Respiratory Infection and Sore Throat Triage",
        "publisher": "CDC Clinical Reference",
        "source_url": "https://www.cdc.gov/groupastrep/diseases-hcp/strep-throat.html",
        "clinical_topic": "Infectious Disease / Respiratory",
        "content": (
            "Viral pharyngitis and common cold syndromes present with scratchy throat, nasal congestion, low-grade fever, "
            "and cough lasting 3 to 7 days. Most episodes are self-limiting. Recommended supportive care includes warm salt water gargles, "
            "oral hydration, honey for cough relief (in patients > 1 year old), and rest. "
            "Red-flag warning signs include inability to swallow liquids, drooling, stridor (wheezing during inhalation), or high persistent fever > 102F."
        ),
    },
    {
        "document_id": "MED-ACUTE-GASTROENTERITIS-04",
        "title": "Clinical Assessment of Acute Diarrhea and Viral Gastroenteritis",
        "publisher": "WHO Primary Care Triage Guidelines",
        "source_url": "https://www.who.int/publications/gastroenteritis-care",
        "clinical_topic": "Gastroenterology / Infection",
        "content": (
            "Acute viral gastroenteritis is characterized by sudden onset nausea, vomiting, watery diarrhea, and low-grade abdominal cramps. "
            "The primary clinical objective is preventing dehydration. Oral Rehydration Solution (ORS) or electrolyte replacement fluids "
            "should be administered in frequent, small sips. Avoid sugary juices or fatty foods. "
            "Emergency warning signs: signs of severe dehydration (lethargy, dry mouth, absence of urination for 8+ hours), "
            "persistent vomiting preventing fluid retention, high fever, or blood in stool."
        ),
    },
    {
        "document_id": "MED-ACUTE-BRONCHITIS-05",
        "title": "Diagnosis and Supportive Treatment of Acute Cough / Bronchitis",
        "publisher": "NICE Clinical Guidelines",
        "source_url": "https://www.nice.org.uk/guidance/bronchitis",
        "clinical_topic": "Pulmonology / Respiratory",
        "content": (
            "Acute bronchitis involves inflammation of the large airways, typically manifesting as persistent cough (with or without sputum) "
            "lasting up to 2-3 weeks following an upper respiratory viral illness. Antibiotics are generally not recommended for uncomplicated acute bronchitis. "
            "Supportive measures: steam inhalation, hydration, honey, and rest. Immediate medical evaluation is warranted if the patient develops "
            "shortness of breath at rest, chest pain, hemoptysis (coughing blood), or symptoms persisting beyond 3 weeks."
        ),
    },
    {
        "document_id": "MED-VIRAL-FEVER-06",
        "title": "Clinical Assessment and Supportive Care of Acute Febrile Illness / Viral Fever",
        "publisher": "WHO Guidelines on Clinical Management of Acute Febrile Illness",
        "source_url": "https://www.who.int/publications/febrile-illness-guidelines",
        "clinical_topic": "Infectious Disease / Febrile Illness",
        "content": (
            "Acute viral fever presents with elevated body temperature, generalized malaise, muscle aches, and body weakness "
            "typically lasting 2 to 5 days without focal localized bacterial infection. Supportive outpatient care focuses on "
            "adequate fluid intake, oral electrolyte replacement, physical cooling with lukewarm sponging, and rest. "
            "Warning signs requiring immediate clinical escalation include body temperature above 102F (38.9C), persistent vomiting, "
            "severe headache with neck rigidity, shortness of breath, confusion, or absence of improvement after 3 days."
        ),
    },
    {
        "document_id": "MED-DENGUE-FEVER-07",
        "title": "Clinical Management of Dengue and Warning Signs Assessment",
        "publisher": "WHO Dengue Guidelines for Diagnosis, Treatment and Control",
        "source_url": "https://www.who.int/publications/dengue-guidelines",
        "clinical_topic": "Infectious Disease / Vector-Borne",
        "content": (
            "Dengue fever presents acutely with high fever, severe headache, retro-orbital pain, prominent joint and bone aches, "
            "and severe fatigue/weakness lasting 2 to 7 days. Critical warning signs indicating severe dengue include persistent abdominal pain, "
            "persistent vomiting, mucosal bleeding, fluid accumulation, and extreme lethargy, requiring urgent hospitalization."
        ),
    },
    {
        "document_id": "MED-INFLUENZA-08",
        "title": "Seasonal Influenza: Clinical Triage and Supportive Care Protocol",
        "publisher": "CDC Clinical Practice Guidelines for Influenza",
        "source_url": "https://www.cdc.gov/flu/professionals/diagnosis/index.htm",
        "clinical_topic": "Infectious Disease / Respiratory",
        "content": (
            "Influenza is characterized by acute abrupt onset of fever, chills, pronounced fatigue and body weakness, cough, "
            "and sore throat lasting 3 to 7 days. First-line supportive care includes strict bed rest, high fluid intake, and droplet isolation. "
            "Patients should seek urgent medical evaluation if experiencing chest pain, dyspnea, cyanosis, or rapid decompensation."
        ),
    },
    {
        "document_id": "AYU-FEVER-JWARA-01",
        "title": "Ayurvedic Clinical Guidance for Jwara (Acute Febrile Illness)",
        "publisher": "Ministry of AYUSH Guidelines / Ayurvedic Pharmacopoeia of India",
        "source_url": "https://ayush.gov.in/guidelines/jwara-clinical-management",
        "clinical_topic": "Complementary Medicine / Ayurveda",
        "content": (
            "In Ayurvedic clinical practice, acute mild fever is classified as Jwara. Traditional supportive care emphasizes "
            "Langhana (light, easily digestible diet such as rice gruel / yavagu, avoiding heavy or oily foods), drinking Shadanga Paniya "
            "(water boiled with dried ginger and nut grass), and fresh Tulsi (Ocimum sanctum) or Giloy (Tinospora cordifolia / Guduchi) decoctions. "
            "Safety & Contraindications: Herbal decoctions are contraindicated in pregnancy without specialist supervision. Giloy must be used with caution "
            "in pre-existing liver disease. Traditional herbs are strictly complementary supportive wellness practices and DO NOT replace conventional "
            "medical care, diagnostic blood testing, or hospital triage for high, persistent, or worsening fevers. Never consume unverified metallic preparations."
        ),
    },
    {
        "document_id": "AYU-RESPIRATORY-KASA-02",
        "title": "Ayurvedic Management of Upper Respiratory Distress and Cough (Kasa)",
        "publisher": "Ministry of AYUSH Clinical Protocols",
        "source_url": "https://ayush.gov.in/guidelines/kasa-respiratory",
        "clinical_topic": "Complementary Medicine / Ayurveda",
        "content": (
            "Traditional Ayurvedic care for upper respiratory distress and throat irritation (Kasa) includes warm water with fresh crushed ginger "
            "(Zingiber officinale), turmeric (Curcuma longa) warm water gargles, and herbal tea with holy basil (Tulsi) for soothing mucosal inflammation. "
            "Contraindications: Avoid pungent herbs in patients with active gastric ulcers or severe reflux. Honey is strictly contraindicated in infants under 1 year. "
            "This guidance is non-substitutive for medical attention if breathing difficulty, stridor, or high fever occurs."
        ),
    },
    {
        "document_id": "AYU-HEADACHE-SHIRASHOOLA-03",
        "title": "Ayurvedic Supportive Care for Tension Headache (Vataja Shirashoola)",
        "publisher": "Central Council for Research in Ayurvedic Sciences (CCRAS)",
        "source_url": "https://ccras.nic.in/content/shirashoola-management",
        "clinical_topic": "Complementary Medicine / Ayurveda",
        "content": (
            "For tension-type and stress headache (Shirashoola), traditional supportive practices recommend localized cooling sandalwood (Chandana) "
            "or mint paste to the temples, gentle temple massage (Shiroabhyanga) with sesame or Brahmi oil, adequate hydration, and calming breathwork (Pranayama). "
            "Contraindications: Do not perform head massage in cases of acute head trauma, high fever, or suspected hypertensive crisis. "
            "Immediate conventional medical emergency evaluation is mandatory for sudden severe 'thunderclap' headache or neurological deficits."
        ),
    },
]


class IngestionSummary:
    def __init__(self, discovered: int, inserted: int, failed: int):
        self.discovered = discovered
        self.inserted = inserted
        self.failed = failed


def ensure_collection_exists(client, collection_name: str, vector_dim: int):
    """Ensures Qdrant collection exists with cosine distance and correct dimensions."""
    collections = client.get_collections()
    existing_names = [c.name for c in collections.collections]
    if collection_name not in existing_names:
        logger.info("Creating collection '%s' with vector size %d and Cosine distance.", collection_name, vector_dim)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_dim,
                distance=models.Distance.COSINE,
            ),
        )


def ingest_curated_knowledge(dry_run: bool = False) -> IngestionSummary:
    """Idempotent ingestion pipeline for verified medical documents into Qdrant."""
    client = get_qdrant_client()
    embeddings = get_embeddings()
    collection_name = settings.qdrant_collection_name
    vector_dim = settings.embedding_dim

    if not dry_run:
        ensure_collection_exists(client, collection_name, vector_dim)

    discovered = len(CURATED_MEDICAL_KNOWLEDGE)
    inserted = 0
    failed = 0

    points = []
    for item in CURATED_MEDICAL_KNOWLEDGE:
        try:
            content = item["content"].strip()
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            chunk_id = f"{item['document_id']}-c1"

            meta = MedicalDocumentMetadata(
                document_id=item["document_id"],
                chunk_id=chunk_id,
                source_id=item["document_id"].split("-")[1],
                title=item["title"],
                publisher=item["publisher"],
                source_url=item.get("source_url"),
                clinical_topic=item.get("clinical_topic"),
                content_hash=content_hash,
                review_status=DocumentReviewStatus.APPROVED,
            )

            if not dry_run:
                # Embed without query instruction (pure passage embedding)
                vector = embeddings.embed_documents([content])[0]
                point_id = int(hashlib.md5(chunk_id.encode("utf-8")).hexdigest()[:15], 16)

                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "page_content": content,
                            "metadata": meta.model_dump(),
                        },
                    )
                )
            inserted += 1
        except Exception as e:
            logger.error("Failed to process document %s: %s", item.get("document_id"), e)
            failed += 1

    if not dry_run and points:
        client.upsert(
            collection_name=collection_name,
            points=points,
        )
        logger.info("Successfully upserted %d verified medical knowledge points into '%s'.", len(points), collection_name)

    return IngestionSummary(discovered=discovered, inserted=inserted, failed=failed)
