"""Knowledge Vector Store - 知识库向量检索模块

此模块封装了FAISS向量库的接口，提供统一的检索功能。
"""

from app.rag.vector_store import FAISSVectorStore, get_vector_store, initialize_vector_store


class KnowledgeVectorStore(FAISSVectorStore):
    """知识库向量存储类，继承自FAISSVectorStore"""
    pass


def get_knowledge_store() -> KnowledgeVectorStore:
    """获取或创建知识库向量存储实例"""
    return get_vector_store()


def init_knowledge_store(directory: str = None) -> KnowledgeVectorStore:
    """初始化知识库向量存储"""
    return initialize_vector_store(directory)


# 保持向后兼容的导出
__all__ = [
    'KnowledgeVectorStore',
    'get_knowledge_store',
    'init_knowledge_store',
]
