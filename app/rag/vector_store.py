from __future__ import annotations

from app.core.config import get_settings


class ChromaVectorStore:
    """Placeholder for later Chroma integration."""

    def __init__(self, persist_dir: str | None = None) -> None:
        self.persist_dir = persist_dir or get_settings().chroma_persist_dir

    def add_documents(self, documents: list[dict]) -> None:
        raise NotImplementedError("Chroma integration is reserved for the next phase.")

    def similarity_search(self, query: str, top_k: int = 5) -> list[dict]:
        raise NotImplementedError("Chroma integration is reserved for the next phase.")
