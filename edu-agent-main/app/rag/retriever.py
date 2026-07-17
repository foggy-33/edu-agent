from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.rag.loader import load_markdown_documents


class KeywordRetriever:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_dir = Path(settings.knowledge_base_dir) / "database_system"

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        documents = load_markdown_documents(self.base_dir)
        terms = self._query_terms(query)
        scored: list[dict[str, Any]] = []
        for document in documents:
            searchable = f"{document['title']}\n{document['content']}".lower()
            score = sum(searchable.count(term) for term in terms)
            if score:
                scored.append({**document, "score": float(score)})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _query_terms(query: str) -> list[str]:
        normalized = query.lower()
        words = re.findall(r"[a-z0-9_]+", normalized)
        chinese_runs = re.findall(r"[\u4e00-\u9fff]+", normalized)
        chinese_terms: list[str] = []
        for run in chinese_runs:
            chinese_terms.extend(run[index : index + 2] for index in range(len(run) - 1))
        return list(dict.fromkeys(words + chinese_terms))
