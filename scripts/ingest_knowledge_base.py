from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.vector_store import initialize_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Markdown files into the RAG store")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    args = parser.parse_args()

    store = initialize_vector_store(
        args.directory,
        clear=args.clear,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(f"Indexed {store.get_documents_count()} chunks in {store.persist_dir}")


if __name__ == "__main__":
    main()
