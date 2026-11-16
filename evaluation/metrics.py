"""
RAGAS Metrics Engine for BluCare+ Medical RAG Evaluation.
Configures and executes the 4 core RAGAS metrics:
1. Faithfulness (Groundedness of claims in context)
2. Answer Relevancy (Directness and relevance of answer to user query)
3. Context Precision (Reranked order of relevant chunks)
4. Context Recall (Retrieved coverage of ground-truth evidence)
"""

import os
import logging
import time
import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Callable
from dotenv import load_dotenv

load_dotenv(".env", override=False)

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms.base import BaseRagasLLM
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_groq import ChatGroq
from langchain_core.prompt_values import PromptValue
from langchain_core.outputs import LLMResult
from ragas.prompt.base import StringIO
from ragas.metrics._faithfulness import StatementFaithfulnessAnswer, StatementGeneratorOutput, NLIStatementOutput
import ragas.prompt.utils

from app.core.config import settings
from app.rag.store import get_embeddings
from evaluation.config import eval_config
from evaluation.rag_adapter import RAGExecutionTrace
from evaluation.dataset_loader import MedicalTestCase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RAGAS Pydantic & Output Parser Compatibility Patches for Groq LLMs
# ---------------------------------------------------------------------------
# 1. Patch StringIO: prevent Pydantic ValidationError when FixOutputFormat receives JSON dict
_orig_sio = StringIO.model_validate
@classmethod
def _safe_sio(cls, obj, *args, **kwargs):
    if isinstance(obj, dict) and "text" not in obj:
        obj = {"text": json.dumps(obj)}
    elif isinstance(obj, str):
        obj = {"text": obj}
    return _orig_sio(obj, *args, **kwargs)
StringIO.model_validate = _safe_sio

# 2. Patch StatementFaithfulnessAnswer: handle missing reason or boolean/string verdicts safely without defaulting to positive
_orig_fa = StatementFaithfulnessAnswer.model_validate
@classmethod
def _safe_fa(cls, obj, *args, **kwargs):
    if isinstance(obj, dict):
        obj = dict(obj)
        if "reason" not in obj or not obj["reason"]:
            obj["reason"] = "Evaluated against evidence context."
        if "verdict" in obj and obj["verdict"] is not None:
            v = obj["verdict"]
            if isinstance(v, str):
                obj["verdict"] = 1 if v.strip().lower() in ("1", "yes", "true", "supported") else 0
            elif isinstance(v, bool):
                obj["verdict"] = 1 if v else 0
            elif isinstance(v, (int, float)):
                obj["verdict"] = 1 if int(v) == 1 else 0
            else:
                obj["verdict"] = 0
        else:
            # Missing verdicts must not be converted into positive results
            obj["verdict"] = 0
    elif isinstance(obj, str):
        obj = {"statement": obj, "reason": "No structured verdict provided by evaluator.", "verdict": 0}
    return _orig_fa(obj, *args, **kwargs)
StatementFaithfulnessAnswer.model_validate = _safe_fa

# 2b. Patch NLIStatementOutput: sanitize statement items and enforce faithful verdict parsing
_orig_nli = NLIStatementOutput.model_validate
@classmethod
def _safe_nli(cls, obj, *args, **kwargs):
    if isinstance(obj, list):
        obj = {"statements": obj}
    elif isinstance(obj, dict):
        obj = dict(obj)
        if "statements" in obj and isinstance(obj["statements"], list):
            valid_stmts = []
            for item in obj["statements"]:
                if isinstance(item, dict):
                    stmt = dict(item)
                    if "statement" not in stmt:
                        continue
                    if "reason" not in stmt or not stmt["reason"]:
                        stmt["reason"] = "Evaluated against evidence context."
                    if "verdict" not in stmt or stmt["verdict"] is None:
                        # Missing verdict is unverified, never default to 1
                        stmt["verdict"] = 0
                    elif isinstance(stmt["verdict"], str):
                        stmt["verdict"] = 1 if stmt["verdict"].strip().lower() in ("1", "yes", "true", "supported") else 0
                    elif isinstance(stmt["verdict"], bool):
                        stmt["verdict"] = 1 if stmt["verdict"] else 0
                    elif isinstance(stmt["verdict"], (int, float)):
                        stmt["verdict"] = 1 if int(stmt["verdict"]) == 1 else 0
                    else:
                        stmt["verdict"] = 0
                    valid_stmts.append(stmt)
                elif isinstance(item, str):
                    valid_stmts.append({"statement": item, "reason": "No structured verdict provided.", "verdict": 0})
            obj["statements"] = valid_stmts
    return _orig_nli(obj, *args, **kwargs)
NLIStatementOutput.model_validate = _safe_nli

# 3. Patch StatementGeneratorOutput: normalize list of statements or dicts
_orig_sgo = StatementGeneratorOutput.model_validate
@classmethod
def _safe_sgo(cls, obj, *args, **kwargs):
    if isinstance(obj, list):
        obj = {"statements": [str(x) if not isinstance(x, dict) else x.get("statement", str(x)) for x in obj]}
    elif isinstance(obj, dict) and "statements" in obj:
        obj = dict(obj)
        stmts = obj["statements"]
        if isinstance(stmts, list):
            obj["statements"] = [str(x) if not isinstance(x, dict) else x.get("statement", str(x)) for x in stmts]
    return _orig_sgo(obj, *args, **kwargs)
StatementGeneratorOutput.model_validate = _safe_sgo

# 4. Patch extract_json: clean trailing commas before closing braces/brackets
_orig_extract_json = ragas.prompt.utils.extract_json
def _robust_extract_json(text: str) -> str:
    res = _orig_extract_json(text)
    return re.sub(r',\s*([}\]])', r'\1', res)
ragas.prompt.utils.extract_json = _robust_extract_json


def groq_finished_parser(response) -> bool:
    """Parses LangChain LLMResult from Groq to handle all standard stop/length finish reasons cleanly."""
    try:
        for g in response.flatten():
            resp = g.generations[0][0]
            if resp.generation_info is not None:
                finish_reason = resp.generation_info.get("finish_reason")
                if finish_reason in ["stop", "STOP", "length", "MAX_TOKENS", "eos_token", None]:
                    return True
        return True
    except Exception:
        return True


class KeyRotatingLangchainLLMWrapper(BaseRagasLLM):
    """
    Paces async LLM generation calls and rotates across available Groq API keys
    with automatic failover on 429 rate limits.
    """
    def __init__(
        self,
        keys: List[str],
        model: str,
        temperature: float = 0.0,
        is_finished_parser: Optional[Callable[[LLMResult], bool]] = None,
    ):
        super().__init__()
        self.keys = keys if keys else [settings.groq_api_key]
        self.model = model
        self.temperature = temperature
        self.is_finished_parser = is_finished_parser
        self._llms = [
            ChatGroq(
                model=model,
                groq_api_key=k,
                temperature=temperature,
                max_tokens=2048,
                max_retries=3,
            )
            for k in self.keys
        ]
        self._idx = 0
        self._lock = asyncio.Lock()

    @property
    def langchain_llm(self) -> ChatGroq:
        return self._llms[self._idx % len(self._llms)]

    def is_finished(self, response: LLMResult) -> bool:
        if self.is_finished_parser is not None:
            return self.is_finished_parser(response)
        return True

    def set_run_config(self, run_config: RunConfig):
        self.run_config = run_config
        for llm in self._llms:
            llm.request_timeout = run_config.timeout

    def _get_next_llm(self) -> ChatGroq:
        llm = self._llms[self._idx % len(self._llms)]
        self._idx = (self._idx + 1) % len(self._llms)
        return llm

    def generate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
        callbacks=None,
    ) -> LLMResult:
        time.sleep(0.4)
        for attempt in range(16):
            llm = self._get_next_llm()
            try:
                result = llm.generate_prompt(prompts=[prompt] * n, stop=stop, callbacks=callbacks)
                generations = [[g[0] for g in result.generations]]
                result.generations = generations
                return result
            except Exception as e:
                err_str = str(e).lower()
                if "rate_limit" in err_str or "429" in err_str or "tpd" in err_str:
                    wait_time = min(1.5 * (attempt + 1), 10.0)
                    logger.warning("Groq key rate limited (%s...). Waiting %.1fs and failing over to next key in pool...", str(llm.groq_api_key)[:10], wait_time)
                    time.sleep(wait_time)
                    continue
                raise e
        raise RuntimeError("All Groq API keys in pool rate limited.")

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
        callbacks=None,
    ) -> LLMResult:
        async with self._lock:
            await asyncio.sleep(0.4)
        for attempt in range(16):
            llm = self._get_next_llm()
            try:
                result = await llm.agenerate_prompt(prompts=[prompt] * n, stop=stop, callbacks=callbacks)
                generations = [[g[0] for g in result.generations]]
                result.generations = generations
                return result
            except Exception as e:
                err_str = str(e).lower()
                if "rate_limit" in err_str or "429" in err_str or "tpd" in err_str:
                    wait_time = min(1.5 * (attempt + 1), 10.0)
                    logger.warning("Groq key rate limited (%s...). Waiting %.1fs and failing over to next key in pool...", str(llm.groq_api_key)[:10], wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                raise e
        raise RuntimeError("All Groq API keys in pool rate limited.")


class MetricsEngine:
    """Configures and runs RAGAS evaluation over execution traces."""

    def __init__(self):
        logger.info(
            "Initializing RAGAS evaluator LLM '%s' (provider: %s, temp: %.1f)",
            eval_config.evaluator_model,
            eval_config.evaluator_provider,
            eval_config.evaluator_temperature,
        )
        raw_keys = os.getenv("GROQ_API_KEYS", "")
        key_pool = [k.strip() for k in raw_keys.split(",") if k.strip()]
        if not key_pool:
            key_pool = [settings.groq_api_key]
        logger.info("RAGAS evaluator initialized with %d Groq API key(s) in pool.", len(key_pool))

        self.wrapped_llm = KeyRotatingLangchainLLMWrapper(
            keys=key_pool,
            model=eval_config.evaluator_model,
            temperature=eval_config.evaluator_temperature,
            is_finished_parser=groq_finished_parser,
        )
        self.wrapped_emb = LangchainEmbeddingsWrapper(get_embeddings())

        # Configure metrics with isolated evaluator LLM & embeddings
        faithfulness.llm = self.wrapped_llm
        answer_relevancy.llm = self.wrapped_llm
        answer_relevancy.embeddings = self.wrapped_emb
        context_precision.llm = self.wrapped_llm
        context_recall.llm = self.wrapped_llm

        self.metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    def evaluate_batch(
        self,
        traces: List[RAGExecutionTrace],
        test_cases: List[MedicalTestCase],
    ) -> pd.DataFrame:
        """
        Executes RAGAS evaluation across a batch of traces and aligns scores with test cases.
        """
        if not traces:
            return pd.DataFrame()

        questions = []
        answers = []
        contexts_list = []
        ground_truths = []
        case_ids = []

        for trace, tc in zip(traces, test_cases):
            case_ids.append(tc.case_id)
            questions.append(tc.user_question)
            answers.append(trace.generated_answer or "No response generated.")

            # RAGAS requires at least one non-empty string in retrieved_contexts
            if trace.retrieved_contexts and len(trace.retrieved_contexts) > 0:
                contexts_list.append(trace.retrieved_contexts)
            else:
                contexts_list.append(["[NO_VERIFIED_MEDICAL_EVIDENCE_FOUND]"])

            # Reference ground truth
            ref = tc.reference_answer or " ".join(tc.expected_facts) or "Evidence not available."
            ground_truths.append(ref)

        data = {
            "user_input": questions,
            "response": answers,
            "retrieved_contexts": contexts_list,
            "reference": ground_truths,
        }

        dataset = Dataset.from_dict(data)

        run_config = RunConfig(
            max_workers=1,
            timeout=180,
            max_retries=5,
            max_wait=30,
        )

        logger.info("Executing RAGAS evaluate on batch of %d cases...", len(traces))
        try:
            eval_result = evaluate(
                dataset,
                metrics=self.metrics,
                run_config=run_config,
                show_progress=False,
            )
            df = eval_result.to_pandas()
        except Exception as e:
            logger.error("RAGAS evaluation failed for batch: %s", e)
            # Fallback zero scores if evaluation API encounters transient failure
            df = pd.DataFrame({
                "faithfulness": [0.0] * len(traces),
                "answer_relevancy": [0.0] * len(traces),
                "context_precision": [0.0] * len(traces),
                "context_recall": [0.0] * len(traces),
            })

        # Inject case metadata and latency measurements
        df["case_id"] = case_ids
        df["clinical_topic"] = [tc.clinical_topic for tc in test_cases]
        df["case_category"] = [tc.case_category for tc in test_cases]
        df["expected_sufficiency"] = [tc.expected_evidence_sufficiency for tc in test_cases]
        df["retrieval_duration_s"] = [t.retrieval_duration_s for t in traces]
        df["generation_duration_s"] = [t.generation_duration_s for t in traces]
        df["retrieved_doc_ids"] = [", ".join(t.reranked_doc_ids) for t in traces]
        df["expected_doc_ids"] = [", ".join(tc.expected_document_ids) for tc in test_cases]
        df["citation_valid"] = [t.citation_valid for t in traces]
        df["is_insufficient_evidence"] = [t.is_insufficient_evidence for t in traces]
        df["error"] = [t.error for t in traces]

        return df
