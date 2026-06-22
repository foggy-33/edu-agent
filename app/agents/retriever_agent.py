from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.rag.retriever import KeywordRetriever
from app.rag.vector_store import get_vector_store


class RetrieverAgent:
    """Hybrid retrieval with keyword fallback and traceable source metadata."""

    def __init__(self, top_k: int | None = None) -> None:
        settings = get_settings()
        self.top_k = top_k or settings.rag_top_k
        self.keyword_retriever = KeywordRetriever()
        self.auto_ingest = settings.rag_auto_ingest

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = state.get("profile", {})
        parts = [state.get("message", ""), state.get("course", "")]
        parts.extend(profile.get("weak_points", []))
        query = " ".join(str(part) for part in parts if part).strip()
        recall_k = max(self.top_k * 2, self.top_k)

        keyword_docs = self.keyword_retriever.search(query, top_k=recall_k)
        vector_docs: list[dict[str, Any]] = []
        vector_error = ""
        try:
            store = get_vector_store()
            if self.auto_ingest:
                store.ensure_indexed()
            vector_docs = store.similarity_search(query, top_k=recall_k)
        except Exception as exc:
            vector_error = str(exc)

        docs = self._merge(keyword_docs, vector_docs)
        return {
            "retrieved_docs": docs,
            "retrieval_meta": {
                "query": query,
                "keyword_count": len(keyword_docs),
                "vector_count": len(vector_docs),
                "mode": "hybrid" if vector_docs else "keyword",
                "vector_error": vector_error,
            },
        }

    def _merge(
        self,
        keyword_docs: list[dict[str, Any]],
        vector_docs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        keyword_scores = self._normalize(keyword_docs)
        vector_scores = self._normalize(vector_docs)
        merged: dict[str, dict[str, Any]] = {}

        for index, document in enumerate(keyword_docs):
            source = str(document.get("source", ""))
            merged[source] = {
                **document,
                "keyword_score": keyword_scores[index],
                "vector_score": 0.0,
                "retrieval_types": ["keyword"],
            }

        for index, document in enumerate(vector_docs):
            source = str(document.get("source", ""))
            if source in merged:
                merged[source]["vector_score"] = vector_scores[index]
                merged[source]["retrieval_types"].append("vector")
                if document.get("content"):
                    merged[source]["content"] = document["content"]
            else:
                merged[source] = {
                    **document,
                    "keyword_score": 0.0,
                    "vector_score": vector_scores[index],
                    "retrieval_types": ["vector"],
                }

        results = []
        for document in merged.values():
            document["combined_score"] = round(
                document["keyword_score"] * 0.4 + document["vector_score"] * 0.6,
                6,
            )
            document["retrieval_types"] = sorted(set(document["retrieval_types"]))
            results.append(document)
        results.sort(key=lambda item: item["combined_score"], reverse=True)
        return results[: self.top_k]

    @staticmethod
    def _normalize(documents: list[dict[str, Any]]) -> list[float]:
        if not documents:
            return []
        scores = [float(document.get("score", 0.0)) for document in documents]
        minimum, maximum = min(scores), max(scores)
        if maximum == minimum:
            return [1.0] * len(scores)
        return [(score - minimum) / (maximum - minimum) for score in scores]
