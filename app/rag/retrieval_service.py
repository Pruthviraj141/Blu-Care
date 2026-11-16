import logging
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from app.core.config import settings
from app.rag.store import get_qdrant_client, get_embeddings, get_reranker, embed_query

logger = logging.getLogger(__name__)


class RetrievalResult:
    def __init__(
        self,
        documents: List[Document],
        query: str,
        status: str,  # success, no_results, insufficient_relevance, degraded
        reranker_applied: bool = False,
    ):
        self.documents = documents
        self.query = query
        self.status = status
        self.reranker_applied = reranker_applied


class MedicalRetrievalService:
    """Unified, measurable medical retrieval service combining BGE dense search and CrossEncoder reranking."""

    @classmethod
    def retrieve(
        cls,
        dense_query: Optional[str] = None,
        limit: Optional[int] = None,
        use_reranker: bool = True,
        score_threshold: Optional[float] = None,
        rerank_query: Optional[str] = None,
        query: Optional[str] = None,
    ) -> RetrievalResult:
        dense_query = dense_query or query or ""
        if not dense_query or not dense_query.strip():
            return RetrievalResult(documents=[], query="", status="no_results")

        final_k = limit or settings.final_k
        fetch_k = settings.fetch_k
        threshold = score_threshold if score_threshold is not None else settings.score_threshold

        client = get_qdrant_client()
        query_vector = embed_query(dense_query)

        try:
            hits = client.search(
                collection_name=settings.qdrant_collection_name,
                query_vector=query_vector,
                limit=fetch_k,
                score_threshold=threshold,
                with_payload=True,
            )
        except Exception as e:
            logger.error("Qdrant search error: %s", e)
            return RetrievalResult(documents=[], query=dense_query, status="vector_store_unavailable")

        if not hits:
            logger.info("No documents passed score threshold %.2f for query '%s'", threshold, dense_query)
            return RetrievalResult(documents=[], query=dense_query, status="no_results")

        candidates = []
        seen_cand_ids = set()
        for h in hits:
            payload = h.payload or {}
            meta = dict(payload.get("metadata", {}))
            meta["_score"] = float(h.score)
            doc_id = meta.get("document_id") or meta.get("id") or str(h.id)
            if doc_id in seen_cand_ids:
                continue
            seen_cand_ids.add(doc_id)
            candidates.append(Document(page_content=payload.get("page_content", ""), metadata=meta))

        if not use_reranker or len(candidates) <= 1:
            return RetrievalResult(
                documents=candidates[:final_k],
                query=dense_query,
                status="success",
                reranker_applied=False,
            )

        # CrossEncoder Reranking
        try:
            reranker = get_reranker()
            scoring_query = (rerank_query or dense_query).strip()
            pairs = [(scoring_query, doc.page_content) for doc in candidates]
            scores = reranker.predict(pairs)
            ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

            reranked_docs = []
            for doc, s in ranked[:final_k]:
                doc.metadata["_rerank_score"] = float(s)
                reranked_docs.append(doc)

            return RetrievalResult(
                documents=reranked_docs,
                query=scoring_query,
                status="success",
                reranker_applied=True,
            )
        except Exception as e:
            logger.warning("CrossEncoder reranking failed (%s). Returning dense candidates in degraded mode.", e)
            return RetrievalResult(
                documents=candidates[:final_k],
                query=dense_query,
                status="reranker_degraded",
                reranker_applied=False,
            )

    retrieve_evidence = retrieve
