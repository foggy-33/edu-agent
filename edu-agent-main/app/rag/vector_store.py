import os
from pathlib import Path
from typing import List, Dict, Optional

from langchain.chains import RetrievalQA
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.vectorstores import FAISS
from openai import OpenAI

from app.core.config import get_settings


class SiliconFlowEmbeddings:
    def __init__(self, api_key: str, base_url: str, model: str):
        # 强制不走代理，直连国内
        self.client = OpenAI(
            api_key=api_key, 
            base_url=base_url
        )
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]
    
    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        return self.embed_documents(texts)
    
    @property
    def embedding_dimension(self) -> int:
        """返回embedding维度，用于FAISS索引"""
        return 1024  # 默认维度，根据实际模型调整


class ChromaVectorStore:
    """Chroma vector store implementation for RAG."""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        """Initialize Chroma vector store.
        
        Args:
            persist_dir: Directory to persist the vector store. Defaults to settings value.
        """
        self.settings = get_settings()
        self.persist_dir = persist_dir or self.settings.chroma_persist_dir
        
        self.embeddings = SiliconFlowEmbeddings(
            api_key=settings.siliconflow_api_key or "sk-placeholder",
            base_url=settings.siliconflow_base_url,
            model=settings.siliconflow_model
        )
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize or load Chroma vector store
        self._initialize_chroma()

    def _initialize_chroma(self) -> None:
        """Initialize Chroma client and load existing data or create new."""
        try:
            self.vector_store = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
            )
            print(f"Chroma vector store loaded from {self.persist_dir}")
        except Exception as e:
            print(f"Error initializing Chroma: {e}")
            raise

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
            
        # Add documents to Chroma
        self.vector_store.add_documents(documents)
        
        # Persist to disk
        self.vector_store.persist()
        
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

    def get_retriever(self, search_kwargs: Optional[Dict] = None) -> object:
        """Get a retriever for use in QA chains.
        
        Args:
            search_kwargs: Additional search parameters.
            
        Returns:
            Chroma retriever object.
        """
        search_kwargs = search_kwargs or {"k": 5}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def get_documents_count(self) -> int:
        """Get the number of documents in the vector store.
        
        Returns:
            Number of documents.
        """
        return len(self.vector_store.get()["documents"])

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self.vector_store.delete_collection()
        self._initialize_chroma()
        print("Vector store cleared")


class FAISSVectorStore:
    """FAISS vector store implementation for RAG."""

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        self.settings = get_settings()
        self.persist_dir = persist_dir or "./faiss_index"
        
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.embeddings = SiliconFlowEmbeddings(
            api_key=self.settings.siliconflow_api_key or "sk-placeholder",
            base_url=self.settings.siliconflow_base_url,
            model=self.settings.siliconflow_model
        )
        
        self._initialize_faiss()

    def _initialize_faiss(self) -> None:
        persist_path = Path(self.persist_dir)
        if persist_path.exists() and (persist_path / "index.faiss").exists():
            self.vector_store = FAISS.load_local(
                self.persist_dir,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"FAISS vector store loaded from {self.persist_dir}")
        else:
            self.vector_store = None
            print(f"FAISS vector store directory created at {self.persist_dir}")

    def load_markdown_files(self, directory: str) -> List[Document]:
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
        if not documents:
            print("No documents to add")
            return
            
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vector_store.add_documents(documents)
        
        self.vector_store.save_local(self.persist_dir)
        print(f"Added {len(documents)} documents to FAISS vector store")

    def add_markdown_directory(self, directory: str) -> None:
        documents = self.load_markdown_files(directory)
        if not documents:
            print("No markdown files found")
            return
        
        chunks = self.split_documents(documents)
        self.add_documents(chunks)

    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict]:
        results = []
        
        if self.vector_store is None:
            print(f"FAISS vector store not initialized, returning empty results")
            return results
        
        try:
            # 直接使用FAISS搜索，避免LangChain包装器问题
            import faiss
            import numpy as np
            
            # 获取query的embedding向量
            query_vec = self.embeddings.embed_query(query)
            query_np = np.array([query_vec], dtype=np.float32)
            
            # 直接搜索FAISS索引
            faiss_index = self.vector_store.index
            distances, indices = faiss_index.search(query_np, top_k)
            
            # 获取文档 - 使用index_to_docstore_id映射
            for i, idx in enumerate(indices[0]):
                if idx >= 0:  # 有效的索引
                    docstore_id = self.vector_store.index_to_docstore_id.get(idx)
                    if docstore_id:
                        doc = self.vector_store.docstore._dict.get(docstore_id)
                        if doc:
                            # LangChain FAISS使用L2距离，转换为相似度
                            similarity = 1.0 / (1.0 + distances[0][i])
                            # 转换source为相对路径，与关键词检索保持一致
                            source = doc.metadata.get("source", "")
                            if source:
                                # 提取knowledge_base之后的部分
                                if "knowledge_base" in source:
                                    source = source.split("knowledge_base")[-1]
                                    source = "knowledge_base" + source
                                # 统一路径分隔符
                                source = source.replace("\\", "/")
                            results.append({
                                "content": doc.page_content,
                                "source": source,
                                "score": float(similarity),
                                "metadata": doc.metadata
                            })
                
            print(f"Found {len(results)} results for query: '{query}'")
            
        except Exception as e:
            print(f"Error during similarity search: {e}")
        
        return results

    def get_retriever(self, search_kwargs: Optional[Dict] = None) -> object:
        search_kwargs = search_kwargs or {"k": 5}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def get_documents_count(self) -> int:
        if self.vector_store is None:
            return 0
        return len(self.vector_store.docstore._dict)

    def clear(self) -> None:
        self.vector_store = None
        for file in Path(self.persist_dir).glob("*"):
            file.unlink()
        print("FAISS vector store cleared")


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
        base_dir = Path(__file__).resolve().parent.parent.parent
        directory = str(base_dir / "knowledge_base" / "database_system")
    
    print(f"Initializing vector store from directory: {directory}")
    store.add_markdown_directory(directory)
    
    return store
