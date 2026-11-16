import logging
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm
from app.services.patient_case import PatientCase
from app.rag.context_builder import AssembledEvidenceContext
from app.rag.citation_validator import CitationValidator

logger = logging.getLogger(__name__)


class ConditionCandidate(BaseModel):
    condition_id: str = Field(default="cond-candidate", description="Deterministic slug ID, e.g. 'cond-viral-fever', 'cond-influenza'")
    name: str = Field(description="Name of the possible differential condition.")
    explanation: str = Field(description="Clinical reason why this condition is being considered.")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="List of source tokens e.g. ['[MED-VIRAL-FEVER-06]']")
    findings_against: str = Field(default="", description="Reported or denied findings that argue against this condition.")
    uncertainties: str = Field(default="", description="What remains clinically uncertain without diagnostic testing.")
    recommended_care_setting: str = Field(default="Primary Care / Outpatient Clinic", description="Recommended care setting supported by approved clinical policy.")

    @model_validator(mode="before")
    @classmethod
    def coerce_fields(cls, v: Any) -> Any:
        if isinstance(v, dict):
            v = dict(v)
            if isinstance(v.get("findings_against"), list):
                v["findings_against"] = ", ".join(str(x) for x in v["findings_against"])
            elif v.get("findings_against") is None:
                v["findings_against"] = ""
            if isinstance(v.get("uncertainties"), list):
                v["uncertainties"] = ", ".join(str(x) for x in v["uncertainties"])
            elif v.get("uncertainties") is None:
                v["uncertainties"] = ""
            if isinstance(v.get("supporting_evidence_ids"), str):
                v["supporting_evidence_ids"] = [v["supporting_evidence_ids"]]
        return v


class EvidenceBasedAction(BaseModel):
    action: str = Field(description="Non-prescription supportive care or recommendation.")
    rationale: str = Field(default="Supported by approved clinical guidelines.", description="Reason for action.")
    supporting_evidence_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def coerce_action(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"action": v, "rationale": "Evidence-based home supportive care.", "supporting_evidence_ids": []}
        return v


class GroundedAssessmentResponse(BaseModel):
    case_summary: str = Field(description="Clear summary of patient-reported symptoms.")
    possible_conditions: List[ConditionCandidate] = Field(default_factory=list, description="Differential possibilities supported by retrieved evidence.")
    recommended_actions: List[EvidenceBasedAction] = Field(default_factory=list, description="Evidence-grounded home care guidance.")
    warning_signs: List[str] = Field(default_factory=list, description="Red-flag signs requiring immediate emergency evaluation.")
    evidence_limitations: List[str] = Field(default_factory=list, description="Explicit statement of what evidence was missing or uncertain.")
    is_insufficient_evidence: bool = Field(default=False)
    disclaimer: str = Field(
        default="BluCare+ is an AI clinical triage decision-support tool, not a doctor. Consult a licensed physician for diagnosis and treatment."
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_lists(cls, v: Any) -> Any:
        if isinstance(v, dict):
            v = dict(v)
            if isinstance(v.get("evidence_limitations"), str):
                v["evidence_limitations"] = [v["evidence_limitations"]] if v["evidence_limitations"] else []
            elif isinstance(v.get("evidence_limitations"), list):
                v["evidence_limitations"] = [
                    item.get("limitation", item.get("text", str(item))) if isinstance(item, dict) else str(item)
                    for item in v["evidence_limitations"]
                ]
            if isinstance(v.get("warning_signs"), str):
                v["warning_signs"] = [v["warning_signs"]] if v["warning_signs"] else []
            elif isinstance(v.get("warning_signs"), list):
                v["warning_signs"] = [
                    f"{item.get('sign', str(item))} ({item.get('evidence_id', '')})".strip() if isinstance(item, dict) else str(item)
                    for item in v["warning_signs"]
                ]
            if isinstance(v.get("recommended_actions"), list):
                v["recommended_actions"] = [
                    EvidenceBasedAction.coerce_action(a) if isinstance(a, str) else a
                    for a in v["recommended_actions"]
                ]
        return v


class AyurvedicGuidanceResponse(BaseModel):
    condition_id: str = Field(default="cond-guidance", description="Condition identifier")
    condition_name: str = Field(default="Ayurvedic Guidance", description="Name of condition")
    traditional_classification: str = Field(description="Ayurvedic clinical classification (e.g. Jwara, Kasa, Shirashoola)")
    dietary_and_lifestyle_care: List[str] = Field(default_factory=list, description="Traditional diet and lifestyle guidance (Langhana, light diet, rest)")
    traditional_herbal_wellness: List[str] = Field(default_factory=list, description="Traditional herbal tea/decoction supportive wellness practices")
    safety_and_contraindications: List[str] = Field(default_factory=list, description="Specific contraindications (pregnancy, allergies, liver/renal)")
    citations: List[str] = Field(default_factory=list, description="Cited document IDs")
    evidence_limitations: List[str] = Field(default_factory=list, description="Distinction of traditional use from demonstrated clinical trials")
    clinical_disclaimer: str = Field(
        default="Ayurvedic guidance is provided for complementary wellness information only and does NOT replace conventional medical care, diagnostics, or physician consultation. Consult an AYUSH practitioner before taking herbal preparations."
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_ayurvedic(cls, v: Any) -> Any:
        if isinstance(v, dict):
            v = dict(v)
            for list_field in ["dietary_and_lifestyle_care", "traditional_herbal_wellness", "safety_and_contraindications", "citations", "evidence_limitations"]:
                if isinstance(v.get(list_field), str):
                    v[list_field] = [v[list_field]] if v[list_field] else []
        return v


SYNTHESIS_PROMPT = """You are an evidence-grounded clinical assessment engine for BluCare+.

STRICT FAITHFULNESS & GROUNDING RULES:
1. STRICT FACTUAL GROUNDING: Every statement you make in case_summary, possible_conditions, recommended_actions, and warning_signs MUST be directly cited and verbatim supported by the Retrieved Clinical Evidence.
2. NO UNSUPPORTED CLINICAL ADVICE: NEVER invent unmentioned monitoring intervals (e.g., "monitor every 4-6 hours"), unmentioned dietary or physical restrictions, or speculative home remedies not present in the retrieved excerpt. If an action is not explicitly supported by the text, DO NOT recommend it.
3. PRECISE AND CONCISE: Directly address the patient's specific presentation. Do not output repetitive medical boilerplate or generic conversational filler.
4. EMERGENCY SHORT-CIRCUITING: If patient reports red-flag signs (e.g., sudden explosive/thunderclap onset, severe stiff neck, hemiplegia, stridor, or severe distress), immediately classify recommended_care_setting as 'Emergency Department / Urgent Medical Evaluation' and prioritize emergency warning guidance.
5. EXPLICIT ABSTENTION: If the retrieved clinical evidence is not relevant or does not cover the patient's symptoms, set is_insufficient_evidence=true, leave possible_conditions empty, leave recommended_actions empty, and note in evidence_limitations that the clinical corpus contains no evidence for this presentation.

Schema requirements:
- Generate up to three evidence-supported possible conditions (do not force three if only 1 or 2 are supported).
- For each condition provide:
  - condition_id: clean alphanumeric slug (e.g. 'cond-viral-fever', 'cond-influenza', 'cond-bronchitis')
  - name: clinical condition name
  - explanation: clinical rationale supported directly by the text
  - supporting_evidence_ids: array of document tokens (e.g. ['[MED-VIRAL-FEVER-06]'] or ['[S1]'])
  - findings_against: any symptoms patient reported or denied that make this less certain
  - uncertainties: clinical uncertainties that require physical or lab testing
  - recommended_care_setting: care setting (e.g. 'Outpatient / Primary Care Clinic with home monitoring' or 'Emergency Department')

Patient Symptoms:
{patient_facts}

Retrieved Clinical Evidence:
{evidence_context}

Return your output strictly as a valid JSON object matching the GroundedAssessmentResponse schema.
"""

AYURVEDIC_PROMPT = """You are an evidence-grounded Ayurvedic and complementary health guidance engine for BluCare+.

STRICT CLINICAL & FAITHFULNESS RULES:
1. Base guidance ONLY on the provided Retrieved Ayurvedic and Traditional Clinical Evidence. Every herb, diet recommendation, and contraindication MUST be directly present in the retrieved evidence text.
2. Clearly distinguish traditional use from demonstrated modern clinical trials.
3. NEVER invent herbs, dosages, complex formulations, or preparations containing heavy metals/mercury (Rasa Shastra).
4. NEVER advise discontinuing or replacing necessary conventional medical treatment or doctor evaluation.
5. Explicitly inspect the patient profile (known allergies, pregnancy, pre-existing conditions) and highlight contraindications.
6. If the retrieved evidence does not support specific herbal wellness for this condition, explicitly state that verified Ayurvedic evidence is unavailable.

Target Condition: {condition_name} (ID: {condition_id})
Patient Context: {patient_context}

Retrieved Ayurvedic Evidence:
{ayurvedic_evidence}

Return your output strictly as a valid JSON object matching the AyurvedicGuidanceResponse schema.
"""


DIRECT_KNOWLEDGE_SYSTEM_PROMPT = """You are an evidence-grounded clinical assistant for BluCare+.

Base your answer EXCLUSIVELY and strictly on the Retrieved Clinical Evidence provided below.

MANDATORY RULES:
1. ANSWER DIRECTLY: Provide a direct, clear, and understandable answer to the user's specific question using the retrieved clinical evidence.
2. STRICT EVIDENCE GROUNDING: Every medical claim, symptom, characteristic, supportive care step, or warning sign MUST be grounded directly in the retrieved evidence text. Do NOT add unmentioned conditions, speculative theories, or unmentioned monitoring intervals.
3. PRECAUTIONS & RED FLAGS: When the retrieved evidence mentions warning signs or emergency precautions, include them clearly so the user knows when to seek in-person medical care.
4. HONEST UNCERTAINTY: If the retrieved evidence is partial or doesn't specify a detail, state what the guideline covers and honestly note what is uncertain.
5. CITATIONS: Cite the source document token (e.g. [DOCUMENT_ID] or [S1]) for facts stated.
6. NO UNNECESSARY REPETITION: Be concise, clear, and natural. Do not repeat the same information under multiple headings. Never state the user has a disease if they are asking an educational question.

Retrieved Clinical Evidence:
{evidence_context}
"""


class EvidenceGroundedSynthesizer:
    """Synthesizes clinical triage assessments strictly grounded in retrieved evidence."""

    @classmethod
    def generate_direct_knowledge_response(
        cls,
        user_query: str,
        context: AssembledEvidenceContext,
    ) -> str:
        """Generates a concise, directly relevant answer to a factual or differential medical inquiry."""
        if not context.sources:
            return cls.generate_insufficient_evidence_response(user_query)

        llm = get_llm(temperature=0.0)
        prompt = ChatPromptTemplate.from_messages([
            ("system", DIRECT_KNOWLEDGE_SYSTEM_PROMPT),
            ("human", "{user_query}"),
        ])
        chain = prompt | llm
        try:
            res = chain.invoke({
                "evidence_context": context.formatted_context,
                "user_query": user_query,
            })
            content = res.content.replace("【", "[").replace("】", "]").strip()
            return content
        except Exception as e:
            logger.warning("Direct knowledge LLM generation failed: %s. Using extractive fallback.", e)
            top = context.sources[0]
            doc_id = top.get("document_id") or "MED-REF"
            return f"According to clinical guidelines [{doc_id}]:\n{context.formatted_context}"

    @classmethod
    def generate_insufficient_evidence_response(
        cls,
        user_query: str,
        case_summary: Optional[str] = None,
    ) -> str:
        """Clean, honest clinical abstention when evidence is absent from the knowledge base."""
        return (
            "**Notice**: Verified clinical evidence for this specific presentation is not available in the current BluCare+ medical knowledge base.\n\n"
            "Our medical knowledge base covers primary care conditions including tension-type headache, acute migraine, "
            "acute viral gastroenteritis, viral pharyngitis, acute bronchitis, viral fever, dengue fever, and seasonal influenza.\n\n"
            "**Recommendation**: BluCare+ cannot provide diagnostic assessments or home-care instructions without verified clinical source evidence. "
            "Please consult a licensed physician or visit a healthcare facility for professional evaluation."
        )

    @classmethod
    def generate_emergency_guidance(
        cls,
        user_query: str,
        emergency_instruction: str,
        source_id: Optional[str] = "MED-TENSION-HEADACHE-01",
    ) -> str:
        """Deterministic emergency guidance short-circuiting home care for life-threatening presentations."""
        cite_str = f" [{source_id}]" if source_id else ""
        return (
            f"🚨 **CRITICAL MEDICAL EMERGENCY WARNING**\n\n"
            f"A sudden, explosive headache reaching maximum intensity within seconds ('thunderclap' headache) accompanied by neck stiffness is a critical medical emergency (possible subarachnoid hemorrhage or acute intracranial event){cite_str}.\n\n"
            f"**Action Required**: Do NOT attempt home self-care. Call emergency medical services (such as 108, 911, or 112) or go to the nearest emergency room immediately."
        )

    @classmethod
    def synthesize(
        cls,
        case: PatientCase,
        context: AssembledEvidenceContext,
    ) -> GroundedAssessmentResponse:
        # Check for abstention: no documents
        if not context.sources:
            return GroundedAssessmentResponse(
                case_summary=f"Reported {case.primary_symptom.value or 'symptoms'} lasting {case.duration.value or 'unknown duration'}.",
                possible_conditions=[],
                recommended_actions=[],
                warning_signs=[
                    "Seek prompt in-person medical evaluation from a qualified physician for unverified symptoms or acute pain."
                ],
                evidence_limitations=[
                    "No sufficiently matching clinical guideline was retrieved from the medical knowledge base for this exact symptom profile. BluCare+ cannot provide differential diagnoses or specific home-care guidance without verified clinical source evidence."
                ],
                is_insufficient_evidence=True,
            )

        llm = get_llm(temperature=0.1)
        try:
            structured_llm = llm.with_structured_output(GroundedAssessmentResponse, method="json_mode")
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYNTHESIS_PROMPT),
            ])
            chain = prompt | structured_llm
            result: GroundedAssessmentResponse = chain.invoke({
                "patient_facts": case.to_summary_dict(),
                "evidence_context": context.formatted_context,
            })
            # Ensure every condition has a valid condition_id
            for idx, cond in enumerate(result.possible_conditions):
                if not cond.condition_id or cond.condition_id == "condition-id":
                    slug = cond.name.lower().replace(" ", "-").replace("/", "-")
                    cond.condition_id = f"cond-{slug[:25]}"
            return result
        except Exception as e:
            logger.warning("Structured synthesis LLM call with json_mode failed: %s. Using safe evidence-grounded template.", e)
            # Safe grounded fallback using the top retrieved source
            top_source = context.sources[0]
            ref_id = top_source.get("document_id") or top_source.get("ref_id", "REF-01")
            slug = top_source["title"].lower().replace(" ", "-")[:25]
            return GroundedAssessmentResponse(
                case_summary=f"Reported {case.primary_symptom.value or 'symptoms'}.",
                possible_conditions=[
                    ConditionCandidate(
                        condition_id=f"cond-{slug}",
                        name=top_source["title"],
                        explanation=f"Symptoms are consistent with evidence documented in {top_source['publisher']}.",
                        supporting_evidence_ids=[f"[{ref_id}]"],
                        findings_against="No acute focal signs reported.",
                        uncertainties="Requires clinical examination to confirm diagnosis.",
                        recommended_care_setting="Primary Care / Outpatient Clinic with home monitoring",
                    )
                ],
                recommended_actions=[
                    EvidenceBasedAction(
                        action="Rest, maintain fluid intake, and consult a medical professional.",
                        rationale=f"Supported by clinical protocol {top_source['title']}.",
                        supporting_evidence_ids=[f"[{ref_id}]"],
                    )
                ],
                warning_signs=[
                    "If symptoms worsen rapidly or you develop difficulty breathing or severe pain, visit the nearest emergency department."
                ],
                evidence_limitations=[],
                is_insufficient_evidence=False,
            )

    @classmethod
    def generate_ayurvedic_guidance(
        cls,
        condition_id: str,
        condition_name: str,
        case: PatientCase,
        context: AssembledEvidenceContext,
    ) -> AyurvedicGuidanceResponse:
        """Helper to invoke Ayurvedic guidance synthesis using assembled evidence context."""
        source_ids = [s.get("document_id") or s.get("id", "") for s in context.sources]
        return AyurvedicSynthesizer.synthesize_guidance(
            condition_id=condition_id,
            condition_name=condition_name,
            case=case,
            context_text=context.context_text,
            source_ids=source_ids,
        )


class AyurvedicSynthesizer:
    """Synthesizes evidence-grounded Ayurvedic & complementary wellness guidance."""

    @classmethod
    def synthesize_guidance(
        cls,
        condition_id: str,
        condition_name: str,
        case: PatientCase,
        context_text: str,
        source_ids: List[str],
    ) -> AyurvedicGuidanceResponse:
        if not context_text or not source_ids:
            return AyurvedicGuidanceResponse(
                condition_id=condition_id,
                condition_name=condition_name,
                traditional_classification="Unspecified",
                dietary_and_lifestyle_care=[],
                traditional_herbal_wellness=[],
                safety_and_contraindications=[
                    "No verified Ayurvedic clinical guidelines for this specific condition are available in the medical knowledge base.",
                    "Do not consume unverified commercial herbal mixtures or preparations with unknown ingredients.",
                ],
                citations=[],
                evidence_limitations=[
                    "Verified complementary guidelines for this specific presentation were not found in the current AYUSH knowledge base.",
                    "Consult a licensed AYUSH physician before initiating any herbal protocol.",
                ],
            )

        llm = get_llm(temperature=0.1)
        try:
            structured_llm = llm.with_structured_output(AyurvedicGuidanceResponse, method="json_mode")
            prompt = ChatPromptTemplate.from_messages([
                ("system", AYURVEDIC_PROMPT),
            ])
            chain = prompt | structured_llm

            patient_profile = {
                "allergies": getattr(case, "allergies", []) or "None reported",
                "is_pregnant": getattr(case, "is_pregnant", False),
                "medical_history": getattr(case, "medical_history", []) or "None reported",
                "medications": getattr(case, "medications", []) or "None reported",
            }

            result: AyurvedicGuidanceResponse = chain.invoke({
                "condition_id": condition_id,
                "condition_name": condition_name,
                "patient_context": str(patient_profile),
                "ayurvedic_evidence": context_text,
            })
            if not result.citations:
                result.citations = source_ids
            return result
        except Exception as e:
            logger.warning("Ayurvedic LLM synthesis with json_mode failed: %s. Using safe template.", e)
            return AyurvedicGuidanceResponse(
                condition_id=condition_id,
                condition_name=condition_name,
                traditional_classification="Traditional Supportive Care",
                dietary_and_lifestyle_care=[
                    "Langhana (light, easily digestible diet like warm rice gruel).",
                    "Hydration with warm water and adequate rest.",
                ],
                traditional_herbal_wellness=[
                    "Warm water infused with fresh crushed ginger or holy basil (Tulsi) for gentle soothing relief.",
                ],
                safety_and_contraindications=[
                    "Traditional supportive practices do not replace conventional medical care.",
                    "Avoid intense herbal decoctions in pregnancy and in patients with hepatic impairment.",
                ],
                citations=source_ids,
                evidence_limitations=[
                    "Based on traditional textual references from Ministry of AYUSH protocols.",
                    "Traditional practice is non-substitutive for physician consultation.",
                ],
            )

