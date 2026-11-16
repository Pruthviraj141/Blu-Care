import logging
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class AssembledEvidenceContext:
    def __init__(
        self,
        formatted_context: str,
        sources: List[Dict[str, Any]],
        total_tokens_approx: int,
    ):
        self.formatted_context = formatted_context
        self.sources = sources
        self.total_tokens_approx = total_tokens_approx

    @property
    def context_text(self) -> str:
        """Compatibility property for synthesizers expecting context_text."""
        return self.formatted_context


def assemble_medical_context(
    retrieved_documents: List[Document],
    max_context_tokens: int = 2500,
) -> AssembledEvidenceContext:
    """
    Assembles a bounded, structured, injection-resistant context for synthesis.
    Assigns stable references [S1], [S2] ... that map back directly to actual document chunks.
    """
    if not retrieved_documents:
        return AssembledEvidenceContext(
            formatted_context="[NO_VERIFIED_MEDICAL_EVIDENCE_FOUND]",
            sources=[],
            total_tokens_approx=0,
        )

    blocks = []
    sources = []
    current_tokens = 0

    for idx, doc in enumerate(retrieved_documents, start=1):
        ref_id = f"S{idx}"
        meta = doc.metadata or {}
        title = meta.get("title") or meta.get("name") or meta.get("source_book") or f"Clinical Reference {idx}"
        publisher = meta.get("publisher") or "Clinical Standard"
        doc_id = meta.get("document_id") or meta.get("id") or f"DOC-{idx}"
        url = meta.get("source_url") or meta.get("url")

        content = doc.page_content.strip()
        # Sanitize against prompt injection: strip any system command directives
        sanitized_content = content.replace("<system>", "").replace("</system>", "").replace("System:", "")

        approx_tokens = len(sanitized_content.split()) * 1.3
        if current_tokens + approx_tokens > max_context_tokens and idx > 1:
            logger.info("Context token budget reached (%d tokens). Truncating at %d documents.", current_tokens, idx - 1)
            break

        current_tokens += approx_tokens
        blocks.append(
            f"[{ref_id}] Title: {title} | Publisher: {publisher} | ID: {doc_id}\n"
            f"Content: {sanitized_content}"
        )

        sources.append({
            "ref_id": ref_id,
            "title": title,
            "publisher": publisher,
            "document_id": doc_id,
            "url": url,
            "score": meta.get("_score") or meta.get("_rerank_score"),
        })

    formatted_text = "\n\n---\n\n".join(blocks)
    return AssembledEvidenceContext(
        formatted_context=formatted_text,
        sources=sources,
        total_tokens_approx=int(current_tokens),
    )
