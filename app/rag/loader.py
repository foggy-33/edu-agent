from __future__ import annotations

from pathlib import Path


def load_markdown_documents(base_dir: str | Path) -> list[dict[str, str]]:
    base_path = Path(base_dir)
    if not base_path.exists():
        return []
    documents: list[dict[str, str]] = []
    for path in sorted(base_path.rglob("*.md")):
        relative_path = path.relative_to(base_path)
        documents.append(
            {
                "title": path.stem,
                "source": str(
                    (Path("knowledge_base") / base_path.name / relative_path).as_posix()
                ),
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return documents
