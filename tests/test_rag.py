from app.rag.retriever import KeywordRetriever
from app.rag.vector_store import LocalHashEmbeddings


def test_local_embeddings_are_deterministic_and_normalized() -> None:
    embeddings = LocalHashEmbeddings(64)
    first = embeddings.embed("数据库 SQL 索引")
    second = embeddings.embed("数据库 SQL 索引")
    assert first == second
    assert abs(sum(value * value for value in first) - 1.0) < 1e-6


def test_keyword_retriever_returns_traceable_sources() -> None:
    results = KeywordRetriever().search("数据库 关系模型", top_k=3)
    assert results
    assert all(item["source"].startswith("knowledge_base/database_system/") for item in results)


def test_keyword_retriever_splits_chinese_and_english_terms() -> None:
    terms = KeywordRetriever._query_terms("数据库 SQL 索引")
    assert "sql" in terms
    assert "数据" in terms
    assert "索引" in terms
