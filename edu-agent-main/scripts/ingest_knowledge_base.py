#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script

This script imports markdown files from the knowledge_base/database_system/ directory
into the FAISS vector store. It provides a simple CLI interface for one-click ingestion.

Usage:
    python scripts/ingest_knowledge_base.py
    python scripts/ingest_knowledge_base.py --clear  # Clear existing vector store first
    python scripts/ingest_knowledge_base.py --directory /path/to/custom/directory
"""

import argparse
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.rag.vector_store import get_vector_store, initialize_vector_store


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest markdown files from knowledge base into FAISS vector store"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vector store before ingestion"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Custom directory to load markdown files from (default: knowledge_base/database_system)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Text chunk size for embedding (default: 500)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlap between chunks (default: 50)"
    )
    return parser.parse_args()


def main():
    """Main entry point for the ingestion script."""
    args = parse_args()
    
    print("=" * 60)
    print("Knowledge Base Ingestion Script (FAISS)")
    print("=" * 60)
    
    try:
        # Get vector store instance
        store = get_vector_store()
        
        # Clear existing data if requested
        if args.clear:
            print("\n[INFO] Clearing existing vector store...")
            store.clear()
        
        # Determine target directory
        if args.directory:
            target_dir = Path(args.directory)
        else:
            target_dir = project_root / "knowledge_base" / "database_system"
        
        # Validate directory
        if not target_dir.exists():
            print(f"[ERROR] Directory not found: {target_dir}")
            sys.exit(1)
        
        print(f"\n[INFO] Target directory: {target_dir}")
        print(f"[INFO] Chunk size: {args.chunk_size}")
        print(f"[INFO] Chunk overlap: {args.chunk_overlap}")
        
        # Count markdown files
        md_files = list(target_dir.rglob("*.md"))
        print(f"\n[INFO] Found {len(md_files)} markdown files")
        for i, file in enumerate(md_files[:5], 1):
            print(f"       - {file.name}")
        if len(md_files) > 5:
            print(f"       ... and {len(md_files) - 5} more files")
        
        # Initialize and ingest
        print("\n[INFO] Starting ingestion...")
        store = initialize_vector_store(str(target_dir))
        
        # Show results
        doc_count = store.get_documents_count()
        print(f"\n[SUCCESS] Ingestion completed!")
        print(f"[INFO] Total documents in vector store: {doc_count}")
        print(f"[INFO] Vector store persisted at: {store.persist_dir}")
        
        # Test search
        print("\n[INFO] Testing similarity search...")
        results = store.similarity_search("What is SQL?", top_k=2)
        print(f"[INFO] Found {len(results)} results for test query")
        for i, result in enumerate(results, 1):
            source = Path(result['source']).name
            content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
            print(f"\n       Result {i}:")
            print(f"       Source: {source}")
            print(f"       Content: {content_preview}")
            print(f"       Score: {result['score']:.4f}")
        
        print("\n" + "=" * 60)
        print("Ingestion completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Ingestion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
