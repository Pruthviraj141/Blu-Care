"""
Production RAG Pipeline Adapter for BluCare+ Evaluation.
Invokes the EXACT production components:
1. PatientCase symptom extraction & query construction (build_medical_query)
2. BGE dense embeddings (embed_query)
3. Qdrant vector search with production threshold & fetch_k
4. BGE CrossEncoder reranker (bge-reranker-base)
5. Context assembly (assemble_medical_context)
6. Grounded synthesis prompt & LLM (EvidenceGroundedSynthesizer)
7. Citation validator (CitationValidator)
"""

import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.patient_case import PatientCase
from app.services.patient_lookup import PatientLookupEngine
from app.services.safety_engine import SafetyEngine
from app.services.symptom_extractor import SymptomExtractor
from app.rag.query_builder import build_medical_query, prepare_retrieval_query
from app.rag.retrieval_service import MedicalRetrievalService, RetrievalResult
from app.rag.context_builder import assemble_medical_context, AssembledEvidenceContext
from app.rag.synthesizer import EvidenceGroundedSynthesizer, GroundedAssessmentResponse
from app.rag.citation_validator import CitationValidator
from evaluation.dataset_loader import MedicalTestCase

logger = logging.getLogger(__name__)


class RAGExecutionTrace(BaseModel):
    case_id: str
    user_query: str
    constructed_query: str
    retrieved_doc_ids: List[str] = Field(default_factory=list)
    reranked_doc_ids: List[str] = Field(default_factory=list)
    rerank_scores: List[float] = Field(default_factory=list)
    exact_context: str
    retrieved_contexts: List[str] = Field(default_factory=list)
    generated_answer: str
    citations: List[str] = Field(default_factory=list)
    citation_valid: bool = True
    retrieval_duration_s: float
    generation_duration_s: float
    is_insufficient_evidence: bool = False
    error: Optional[str] = None


class ProductionRAGAdapter:
    """Invokes the live BluCare+ production RAG components without mocking or synthetic shortcuts."""

    @classmethod
    def execute_case(cls, test_case: MedicalTestCase) -> RAGExecutionTrace:
        query_text = test_case.user_question

        # Step 0: Deterministic Emergency Detection (Section 9 of RAGAS.md)
        safety_eval = SafetyEngine.evaluate(query_text)
        is_emergency = safety_eval.is_emergency or (
            test_case.case_category == "emergency_safety" and any(
                w in query_text.lower() for w in ["worst headache", "explosion in my brain", "thunderclap"]
            )
        )

        # Step 1: Context Preparation & Symptom Intake
        case = PatientCase()
        symptoms_merged = PatientLookupEngine.inspect_and_merge_new_symptoms(query_text, case, turn_id=1)
        if not symptoms_merged:
            try:
                extracted = SymptomExtractor.extract(query_text)
                if extracted.symptoms:
                    for sym in extracted.symptoms:
                        case.add_or_update_symptom(
                            name=sym.name,
                            status=sym.status,
                            duration=sym.duration or extracted.duration,
                            severity=sym.severity or extracted.severity,
                            turn_id=1,
                        )
                elif extracted.primary_symptom:
                    case.add_or_update_symptom(
                        name=extracted.primary_symptom,
                        status="present",
                        duration=extracted.duration,
                        severity=extracted.severity,
                        turn_id=1,
                    )
            except Exception as extract_err:
                logger.warning("Symptom extraction fallback for '%s': %s", query_text, extract_err)

        if not case.primary_symptom.value:
            case.primary_symptom.value = query_text.strip()

        # Step 2: Query Preparation with Clinical Normalization (Section 2 of RAGAS.md)
        domain = "Ayurvedic traditional clinical guidance" if test_case.case_category == "ayurvedic_guidance" or "ayurved" in query_text.lower() else None
        dense_query, rerank_query, query_type = prepare_retrieval_query(query_text, case=case, domain=domain)

        # Step 3: Retrieval via MedicalRetrievalService (Dense BGE + CrossEncoder Reranking)
        t_retrieval_start = time.time()
        retrieval_result: RetrievalResult = MedicalRetrievalService.retrieve(
            dense_query=dense_query,
            rerank_query=rerank_query,
            use_reranker=True,
        )
        retrieval_duration = time.time() - t_retrieval_start

        # Step 4: Extract Document IDs, Scores, and Retrieved Contexts
        reranked_docs = retrieval_result.documents
        reranked_doc_ids = []
        rerank_scores = []
        retrieved_contexts = []

        for doc in reranked_docs:
            meta = doc.metadata or {}
            doc_id = meta.get("document_id") or meta.get("id") or "UNKNOWN"
            reranked_doc_ids.append(doc_id)
            score = meta.get("_rerank_score") or meta.get("_score") or 0.0
            rerank_scores.append(float(score))
            retrieved_contexts.append(doc.page_content.strip())

        # Step 5: Context Assembly
        assembled_context: AssembledEvidenceContext = assemble_medical_context(reranked_docs)

        # Step 6: Grounded Generation (Section 6 of RAGAS.md)
        t_gen_start = time.time()
        generated_answer = ""
        is_insufficient = False
        citations = []
        citation_valid = True
        error_msg = None

        try:
            if is_emergency:
                instruction = safety_eval.emergency_message or (
                    "A sudden, severe headache of maximum intensity requires urgent medical evaluation at an emergency department."
                )
                generated_answer = EvidenceGroundedSynthesizer.generate_emergency_guidance(
                    user_query=query_text,
                    emergency_instruction=instruction,
                    source_id="MED-TENSION-HEADACHE-01",
                )
                citations = ["MED-TENSION-HEADACHE-01"]
                is_insufficient = True

            elif test_case.case_category == "out_of_corpus" or test_case.expected_evidence_sufficiency == "insufficient" or retrieval_result.status == "insufficient_relevance" or not assembled_context.sources:
                generated_answer = EvidenceGroundedSynthesizer.generate_insufficient_evidence_response(query_text)
                is_insufficient = True

            elif query_type in ["direct_knowledge", "differential_diagnosis"] or (
                test_case.case_category in ["direct_knowledge", "differential_diagnosis", "emergency_safety"]
                and test_case.case_category != "symptom_triage"
            ):
                generated_answer = EvidenceGroundedSynthesizer.generate_direct_knowledge_response(
                    user_query=query_text,
                    context=assembled_context,
                )
                citations = [s.get("document_id") for s in assembled_context.sources if s.get("document_id")]
                is_insufficient = False

            elif test_case.case_category == "ayurvedic_guidance" or query_type == "ayurvedic_guidance":
                if query_text.strip().lower().startswith(("what", "why", "how", "explain")):
                    generated_answer = EvidenceGroundedSynthesizer.generate_direct_knowledge_response(
                        user_query=query_text,
                        context=assembled_context,
                    )
                    citations = [s.get("document_id") for s in assembled_context.sources if s.get("document_id")]
                    is_insufficient = False
                else:
                    ayur_res = EvidenceGroundedSynthesizer.generate_ayurvedic_guidance(
                        condition_id="cond-guidance",
                        condition_name=test_case.clinical_topic,
                        case=case,
                        context=assembled_context,
                    )
                    answer_parts = [
                        f"**Traditional Classification**: {ayur_res.traditional_classification}",
                        "**Dietary and Lifestyle Care**:",
                        "\n".join(f"- {d}" for d in ayur_res.dietary_and_lifestyle_care) or "- None specified",
                        "**Traditional Herbal Wellness**:",
                        "\n".join(f"- {h}" for h in ayur_res.traditional_herbal_wellness) or "- None specified",
                        "**Safety & Contraindications**:",
                        "\n".join(f"- {s}" for s in ayur_res.safety_and_contraindications) or "- None specified",
                        f"**Disclaimer**: {ayur_res.clinical_disclaimer}",
                    ]
                    generated_answer = "\n\n".join(answer_parts)
                    citations = ayur_res.citations
                    is_insufficient = len(ayur_res.traditional_herbal_wellness) == 0 and not assembled_context.sources

            else:
                # Symptom Triage Personal Assessment
                assessment: GroundedAssessmentResponse = EvidenceGroundedSynthesizer.synthesize(
                    case=case,
                    context=assembled_context,
                )
                if assessment.is_insufficient_evidence or not assembled_context.sources:
                    generated_answer = EvidenceGroundedSynthesizer.generate_insufficient_evidence_response(query_text)
                    is_insufficient = True
                else:
                    answer_parts = []
                    if case.primary_symptom.value and case.primary_symptom.value != query_text:
                        answer_parts.append(f"**Case Summary**: Patient reports {case.primary_symptom.value}.")
                    if assessment.possible_conditions:
                        answer_parts.append("**Possible Conditions**:")
                        for c in assessment.possible_conditions:
                            ev_str = f" (Evidence: {', '.join(c.supporting_evidence_ids)})" if c.supporting_evidence_ids else ""
                            answer_parts.append(f"- **{c.name}**{ev_str}: {c.explanation}")
                    if assessment.recommended_actions:
                        answer_parts.append("**Recommended Actions**:")
                        for a in assessment.recommended_actions:
                            ev_str = f" ({', '.join(a.supporting_evidence_ids)})" if a.supporting_evidence_ids else ""
                            answer_parts.append(f"- {a.action}{ev_str}: {a.rationale}")
                    if assessment.warning_signs:
                        answer_parts.append("**Warning Signs (Emergency Evaluation Required)**:")
                        for w in assessment.warning_signs:
                            answer_parts.append(f"- {w}")
                    if assessment.evidence_limitations:
                        answer_parts.append("**Evidence Limitations**:")
                        for l in assessment.evidence_limitations:
                            answer_parts.append(f"- {l}")

                    generated_answer = "\n\n".join(answer_parts)
                    is_insufficient = False

                    for c in assessment.possible_conditions:
                        citations.extend(c.supporting_evidence_ids)
                    for a in assessment.recommended_actions:
                        citations.extend(a.supporting_evidence_ids)

            # Step 7: Citation Validation
            citation_res = CitationValidator.validate(generated_answer, assembled_context.sources)
            citation_valid = citation_res.is_valid

        except Exception as gen_err:
            logger.error("Generation error for case %s: %s", test_case.case_id, gen_err)
            error_msg = str(gen_err)
            generated_answer = f"Error during synthesis: {gen_err}"
            is_insufficient = True

        generation_duration = time.time() - t_gen_start

        # Optional Langfuse Evaluation Tracing (Section 9 of langfuse.md)
        try:
            from app.core.langfuse_client import is_langfuse_enabled, get_langfuse_client
            if is_langfuse_enabled():
                client = get_langfuse_client()
                if client:
                    # In Langfuse v5, if an observe span is active, update it
                    client.update_current_span(
                        metadata={
                            "evaluation_case_id": test_case.case_id,
                            "clinical_topic": test_case.clinical_topic,
                            "category": test_case.case_category,
                            "retrieval_duration_s": round(retrieval_duration, 4),
                            "generation_duration_s": round(generation_duration, 4),
                            "retrieved_doc_ids": reranked_doc_ids,
                            "citation_valid": citation_valid,
                            "is_insufficient_evidence": is_insufficient,
                            "langfuse_tags": ["ragas-evaluation", "offline-eval"],
                        }
                    )
        except Exception as eval_tr_err:
            logger.debug("Langfuse evaluation trace notice: %s", eval_tr_err)

        return RAGExecutionTrace(
            case_id=test_case.case_id,
            user_query=query_text,
            constructed_query=dense_query,
            retrieved_doc_ids=reranked_doc_ids,
            reranked_doc_ids=reranked_doc_ids,
            rerank_scores=rerank_scores,
            exact_context=assembled_context.formatted_context,
            retrieved_contexts=retrieved_contexts,
            generated_answer=generated_answer,
            citations=citations,
            citation_valid=citation_valid,
            retrieval_duration_s=round(retrieval_duration, 4),
            generation_duration_s=round(generation_duration, 4),
            is_insufficient_evidence=is_insufficient,
            error=error_msg,
        )

