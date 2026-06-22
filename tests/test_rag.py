from app.agents.retriever_agent import RetrieverAgent
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


def test_hybrid_merge_combines_keyword_and_vector_scores() -> None:
    agent = RetrieverAgent(top_k=2)
    results = agent._merge(
        [{"source": "a.md", "title": "A", "content": "keyword", "score": 3}],
        [
            {"source": "a.md", "title": "A", "content": "vector chunk", "score": 0.9},
            {"source": "b.md", "title": "B", "content": "vector only", "score": 0.5},
        ],
    )
    assert results[0]["source"] == "a.md"
    assert results[0]["retrieval_types"] == ["keyword", "vector"]
    assert results[0]["content"] == "vector chunk"
