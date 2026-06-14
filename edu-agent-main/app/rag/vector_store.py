from __future__ import annotations

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings

from app.core.config import get_settings


class LocalEmbeddings(Embeddings):
    """Simple local embeddings using hash-based vectors - no network required."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def _text_to_vector(self, text: str) -> List[float]:
        """Convert text to a deterministic vector using hash."""
        import hashlib
        # Create a deterministic vector from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        np.random.seed(int(text_hash[:8], 16))
        vector = np.random.randn(self.dimension).astype(np.float32)
        # Normalize
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return [self._text_to_vector(text) for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a query."""
        return self._text_to_vector(text)


class FAISSVectorStore:
    """FAISS vector store implementation for RAG - works without SQLite dependencies."""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        """Initialize FAISS vector store.
        
        Args:
            persist_dir: Directory to persist the vector store. Defaults to settings value.
        """
        self.settings = get_settings()
        self.persist_dir = persist_dir or self.settings.chroma_persist_dir or "./faiss_index"
        
        # Use local embeddings (no network required)
        # Can be replaced with OpenAIEmbeddings when API key is configured
        self.embeddings = LocalEmbeddings(dimension=384)
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize FAISS
        self._initialize_faiss()

    def _initialize_faiss(self) -> None:
        """Initialize FAISS and load existing data or create new."""
        index_path = Path(self.persist_dir) / "index.faiss"
        pkl_path = Path(self.persist_dir) / "index.pkl"
        
        try:
            if index_path.exists() and pkl_path.exists():
                # Load existing FAISS index
                self.vector_store = FAISS.load_local(
                    folder_path=str(self.persist_dir),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"FAISS vector store loaded from {self.persist_dir}")
            else:
                # Create new FAISS index with a placeholder
                self.vector_store = FAISS.from_texts(
                    texts=[""],
                    embedding=self.embeddings
                )
                # Remove the placeholder document
                self.vector_store.delete([self.vector_store.index_to_docstore_id[0]])
                print("FAISS vector store initialized (new)")
        except Exception as e:
            print(f"Error initializing FAISS: {e}")
            # Create new index on error
            self.vector_store = FAISS.from_texts(
                texts=[""],
                embedding=self.embeddings
            )
            try:
                self.vector_store.delete([self.vector_store.index_to_docstore_id[0]])
            except:
                pass
            print("FAISS vector store initialized (new, after error)")

    def _save_faiss(self) -> None:
        """Save FAISS index to disk."""
        self.vector_store.save_local(folder_path=str(self.persist_dir))
        print(f"FAISS vector store saved to {self.persist_dir}")

    def load_markdown_files(self, directory: str) -> List[Document]:
        """Load all markdown files from a directory.
        
        Args:
            directory: Path to the directory containing markdown files.
            
        Returns:
            List of Document objects loaded from markdown files.
        """
        loader = DirectoryLoader(
            directory,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        
        documents = loader.load()
        print(f"Loaded {len(documents)} markdown files from {directory}")
        return documents

    def split_documents(self, documents: List[Document], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
        """Split documents into smaller chunks for embedding.
        
        Args:
            documents: List of documents to split.
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            
        Returns:
            List of split document chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks

    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add.
        """
        if not documents:
            print("No documents to add")
            return
        
        # Add documents to FAISS
        self.vector_store.add_documents(documents)
        
        # Persist to disk
        self._save_faiss()
        
        print(f"Added {len(documents)} documents to vector store")

    def add_markdown_directory(self, directory: str) -> None:
        """Load markdown files from directory, split, and add to vector store.
        
        Args:
            directory: Path to directory containing markdown files.
        """
        # Load documents
        documents = self.load_markdown_files(directory)
        
        if not documents:
            print("No markdown files found")
            return
        
        # Split into chunks
        chunks = self.split_documents(documents)
        
        # Add to vector store
        self.add_documents(chunks)

    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform similarity search and return results with sources.
        
        Args:
            query: Search query string.
            top_k: Number of results to return.
            
        Returns:
            List of dictionaries containing 'content', 'source', and 'score'.
        """
        results = []
        
        try:
            # Perform similarity search
            docs = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "score": float(score),
                    "metadata": doc.metadata
                })
                
            print(f"Found {len(results)} results for query: '{query}'")
            
        except Exception as e:
            print(f"Error during similarity search: {e}")
            raise
        
        return results

    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search documents by query - returns Document objects (LangChain style).
        
        Args:
            query: Search query string.
            k: Number of results to return.
            
        Returns:
            List of Document objects.
        """
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            print(f"Found {len(docs)} results for query: '{query}'")
            return docs
        except Exception as e:
            print(f"Error during search: {e}")
            raise

    def get_retriever(self, search_kwargs: Optional[Dict] = None) -> object:
        """Get a retriever for use in QA chains.
        
        Args:
            search_kwargs: Additional search parameters.
            
        Returns:
            FAISS retriever object.
        """
        search_kwargs = search_kwargs or {"k": 5}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def get_documents_count(self) -> int:
        """Get the number of documents in the vector store.
        
        Returns:
            Number of documents.
        """
        try:
            return self.vector_store.index.ntotal
        except:
            return 0

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        # Create new empty index
        self.vector_store = FAISS.from_texts(
            texts=[""],
            embedding=self.embeddings
        )
        try:
            self.vector_store.delete([self.vector_store.index_to_docstore_id[0]])
        except:
            pass
        # Save empty index
        self._save_faiss()
        print("Vector store cleared")


# Initialize global vector store instance
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """Get or create the global vector store instance.
    
    Returns:
        Singleton instance of FAISSVectorStore.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore()
    return _vector_store


def initialize_vector_store(directory: Optional[str] = None) -> FAISSVectorStore:
    """Initialize vector store and load documents from knowledge base.
    
    Args:
        directory: Directory to load markdown files from. 
                   Defaults to knowledge_base/database_system.
                   
    Returns:
        Initialized FAISSVectorStore instance.
    """
    store = get_vector_store()
    
    if directory is None:
        # Use default knowledge base directory
        base_dir = Path(__file__).resolve().parent.parent.parent
        directory = str(base_dir / "knowledge_base" / "database_system")
    
    print(f"Initializing vector store from directory: {directory}")
    store.add_markdown_directory(directory)
    
    return store
