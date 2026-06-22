from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.rag.loader import load_markdown_documents


class LocalHashEmbeddings:
    """Deterministic local embeddings suitable for an offline course knowledge base."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = self._tokens(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = text.lower()
        words = re.findall(r"[a-z0-9_]+", normalized)
        chinese_runs = re.findall(r"[\u4e00-\u9fff]+", normalized)
        chinese_tokens: list[str] = []
        for run in chinese_runs:
            chinese_tokens.extend(run)
            chinese_tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
        return words + chinese_tokens


class ChromaVectorStore:
    """Persistent Chroma store with local embeddings and source-aware results."""

    collection_name = "database_system"

    def __init__(self, persist_dir: str | None = None) -> None:
        settings = get_settings()
        self.persist_dir = Path(persist_dir or settings.chroma_persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings = LocalHashEmbeddings(settings.rag_embedding_dimension)

        import chromadb

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None,
        )

    def ensure_indexed(self, directory: str | Path | None = None) -> int:
        settings = get_settings()
        base_dir = Path(directory or settings.knowledge_base_dir) / "database_system"
        fingerprint = self._directory_fingerprint(base_dir)
        fingerprint_file = self.persist_dir / ".knowledge_fingerprint"
        stored_fingerprint = (
            fingerprint_file.read_text(encoding="utf-8")
            if fingerprint_file.exists()
            else ""
        )
        if self.collection.count() > 0 and stored_fingerprint == fingerprint:
            return self.collection.count()
        self.clear()
        count = self.add_markdown_directory(base_dir)
        fingerprint_file.write_text(fingerprint, encoding="utf-8")
        return count

    def add_markdown_directory(
        self,
        directory: str | Path,
        *,
        chunk_size: int = 700,
        chunk_overlap: int = 100,
    ) -> int:
        documents = load_markdown_documents(directory)
        chunks: list[dict[str, str]] = []
        for document in documents:
            for index, content in enumerate(
                self._split_text(document["content"], chunk_size, chunk_overlap)
            ):
                chunks.append(
                    {
                        "id": hashlib.sha256(
                            f"{document['source']}:{index}:{content}".encode("utf-8")
                        ).hexdigest(),
                        "content": content,
                        "source": document["source"],
                        "title": document["title"],
                    }
                )

        if not chunks:
            return 0

        batch_size = 128
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            self.collection.upsert(
                ids=[item["id"] for item in batch],
                documents=[item["content"] for item in batch],
                metadatas=[
                    {"source": item["source"], "title": item["title"]} for item in batch
                ],
                embeddings=[self.embeddings.embed(item["content"]) for item in batch],
            )
        return self.collection.count()

    def similarity_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not query.strip() or self.collection.count() == 0:
            return []

        result = self.collection.query(
            query_embeddings=[self.embeddings.embed(query)],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        matches: list[dict[str, Any]] = []
        for content, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            matches.append(
                {
                    "content": content,
                    "source": str(metadata.get("source", "")),
                    "title": str(metadata.get("title", "")),
                    "score": 1.0 / (1.0 + max(0.0, float(distance))),
                    "metadata": metadata,
                }
            )
        return matches

    def get_documents_count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None,
        )

    @staticmethod
    def _directory_fingerprint(directory: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(directory.rglob("*.md")):
            digest.update(str(path.relative_to(directory)).encode("utf-8"))
            digest.update(path.read_bytes())
        return digest.hexdigest()

    @staticmethod
    def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_size must be positive and chunk_overlap smaller than it")
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip()
            if current and len(candidate) > chunk_size:
                chunks.append(current)
                current = f"{current[-chunk_overlap:]}\n\n{paragraph}".strip()
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks


_vector_store: ChromaVectorStore | None = None


def get_vector_store() -> ChromaVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store


def initialize_vector_store(
    directory: str | Path | None = None,
    *,
    clear: bool = False,
    chunk_size: int = 700,
    chunk_overlap: int = 100,
) -> ChromaVectorStore:
    store = get_vector_store()
    if clear:
        store.clear()
    settings = get_settings()
    target = Path(directory) if directory else Path(settings.knowledge_base_dir) / "database_system"
    store.add_markdown_directory(
        target,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return store
