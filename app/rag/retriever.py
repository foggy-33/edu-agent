from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.rag.loader import load_markdown_documents


class KeywordRetriever:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_dir = Path(settings.knowledge_base_dir) / "database_system"

    def search(self, query: str, top_k: int = 5) -> list[dict[str, str | int]]:
        documents = load_markdown_documents(self.base_dir)
        terms = [term for term in query.replace("、", " ").replace("，", " ").split() if term]

        scored = []
        for doc in documents:
            content = f"{doc['title']}\n{doc['content']}"
            score = sum(content.count(term) for term in terms)
            if score > 0:
                scored.append({**doc, "score": score})

        if not scored:
            scored = [{**doc, "score": 0} for doc in documents[:top_k]]

        scored.sort(key=lambda item: int(item["score"]), reverse=True)
        return scored[:top_k]
