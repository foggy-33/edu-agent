from __future__ import annotations

from typing import Any

from app.rag.retriever import KeywordRetriever


class RetrieverAgent:
    def __init__(self) -> None:
        self.retriever = KeywordRetriever()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = state.get("profile", {})
        query_terms = profile.get("weak_points") or [state.get("message", "")]
        docs = self.retriever.search(" ".join(query_terms), top_k=5)
        return {"retrieved_docs": docs}
