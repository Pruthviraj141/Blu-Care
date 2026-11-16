import logging
import re
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class CitationValidationResult:
    def __init__(
        self,
        is_valid: bool,
        referenced_sources: List[Dict[str, Any]],
        unsupported_citations: List[str],
        claims_grounded: bool,
    ):
        self.is_valid = is_valid
        self.referenced_sources = referenced_sources
        self.unsupported_citations = unsupported_citations
        self.claims_grounded = claims_grounded


class CitationValidator:
    """
    Deterministic validator verifying that every medical citation in generated text
    corresponds to an actual retrieved document present in the context.
    """

    @classmethod
    def validate(
        cls,
        text: str,
        available_sources: List[Dict[str, Any]],
    ) -> CitationValidationResult:
        if not text:
            return CitationValidationResult(is_valid=True, referenced_sources=[], unsupported_citations=[], claims_grounded=True)

        # Normalize Unicode full-width brackets from certain LLMs
        normalized_text = text.replace("【", "[").replace("】", "]")

        # Detect citation tokens like [S1], [S2], [Source 1], and canonical doc IDs like [MED-TENSION-HEADACHE-01]
        token_pattern = r"\[(?:S|Source\s*)(\d+)\]"
        doc_pattern = r"\[((?:MED|AYU)-[A-Z0-9\-]+)\]"

        token_matches = re.findall(token_pattern, normalized_text, re.IGNORECASE)
        doc_matches = re.findall(doc_pattern, normalized_text)

        source_map = {}
        for s in available_sources:
            ref_id = s.get("ref_id", "")
            doc_id = s.get("document_id", "")
            num_match = re.search(r"\d+", ref_id)
            if num_match:
                source_map[num_match.group(0)] = s
            if ref_id:
                source_map[ref_id.upper()] = s
            if doc_id:
                source_map[doc_id.upper()] = s

        referenced_sources = []
        unsupported_citations = []
        seen_keys = set()

        for num in token_matches:
            if num in source_map:
                if num not in seen_keys:
                    referenced_sources.append(source_map[num])
                    seen_keys.add(num)
            else:
                unsupported_citations.append(f"[S{num}]")

        for did in doc_matches:
            did_key = did.upper()
            if did_key in source_map:
                if did_key not in seen_keys:
                    referenced_sources.append(source_map[did_key])
                    seen_keys.add(did_key)
            else:
                unsupported_citations.append(f"[{did}]")

        is_valid = len(unsupported_citations) == 0
        claims_grounded = len(referenced_sources) > 0 if available_sources else False

        if not is_valid:
            logger.warning("Synthesis generated unsupported citations: %s", unsupported_citations)

        return CitationValidationResult(
            is_valid=is_valid,
            referenced_sources=referenced_sources,
            unsupported_citations=unsupported_citations,
            claims_grounded=claims_grounded,
        )
