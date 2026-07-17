from typing import Any, Dict, List

from app.rag.retriever import KeywordRetriever
from app.rag.vector_store import get_vector_store


class RetrieverAgent:
    def __init__(self, top_k=5):
        self.keyword_retriever = KeywordRetriever()
        self.top_k = top_k

    def _normalize_score(self, score, min_score, max_score):
        if max_score == min_score:
            return 1.0
        return (score - min_score) / (max_score - min_score)

    def _rerank_and_merge(self, keyword_results, vector_results, final_k=5):
        doc_map = {}
        
        if keyword_results:
            kw_scores = [d.get("score", 0) for d in keyword_results]
            kw_min = min(kw_scores)
            kw_max = max(kw_scores)
            for doc in keyword_results:
                source = doc.get("source", "")
                if source not in doc_map:
                    doc_map[source] = {
                        "content": doc.get("content", ""),
                        "source": source,
                        "title": doc.get("title", ""),
                        "keyword_score": doc.get("score", 0),
                        "keyword_score_norm": self._normalize_score(doc.get("score", 0), kw_min, kw_max),
                        "vector_score": None,
                        "vector_score_norm": 0.0,
                        "types": ["keyword"],
                    }
                else:
                    doc_map[source]["types"].append("keyword")
        
        if vector_results:
            vec_scores = [d.get("score", 0) for d in vector_results]
            vec_min = min(vec_scores)
            vec_max = max(vec_scores)
            for doc in vector_results:
                source = doc.get("source", "")
                content = doc.get("content", "")
                if source not in doc_map:
                    title = doc.get("title", "") or self._extract_title(content)
                    doc_map[source] = {
                        "content": content,
                        "source": source,
                        "title": title,
                        "keyword_score": 0,
                        "keyword_score_norm": 0.0,
                        "vector_score": doc.get("score", 0),
                        "vector_score_norm": self._normalize_score(doc.get("score", 0), vec_min, vec_max),
                        "types": ["vector"],
                    }
                else:
                    doc_map[source]["vector_score"] = doc.get("score", 0)
                    doc_map[source]["vector_score_norm"] = self._normalize_score(doc.get("score", 0), vec_min, vec_max)
                    doc_map[source]["types"].append("vector")
        
        WEIGHT_KEYWORD = 0.4
        WEIGHT_VECTOR = 0.6
        
        merged = []
        for source, doc in doc_map.items():
            combined_score = (
                doc["keyword_score_norm"] * WEIGHT_KEYWORD +
                doc["vector_score_norm"] * WEIGHT_VECTOR
            )
            merged.append({
                "content": doc["content"],
                "source": doc["source"],
                "title": doc["title"],
                "keyword_score": doc["keyword_score"],
                "vector_score": doc["vector_score"],
                "combined_score": combined_score,
                "retrieval_types": list(set(doc["types"])),
            })
        
        merged.sort(key=lambda x: x["combined_score"], reverse=True)
        return merged[:final_k]

    def _extract_title(self, content):
        if not content:
            return ""
        lines = content.strip().split("\n")
        first_line = lines[0] if lines else ""
        return first_line.lstrip("# ").strip()

    def run(self, state):
        profile = state.get("profile", {})
        query = state.get("message", "")
        
        weak_points = profile.get("weak_points", [])
        if weak_points:
            query = query + " " + " ".join(weak_points)
        
        recall_k = self.top_k * 2
        
        keyword_docs = self.keyword_retriever.search(query, top_k=recall_k)
        
        vector_docs = []
        try:
            vector_store = get_vector_store()
            vector_results = vector_store.similarity_search(query, top_k=recall_k)
            for result in vector_results:
                vector_docs.append({
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "score": result.get("score", 0.0),
                    "title": result.get("metadata", {}).get("title", ""),
                })
        except Exception as e:
            print(f"向量检索失败: {e}")
        
        merged_docs = self._rerank_and_merge(
            keyword_results=keyword_docs,
            vector_results=vector_docs,
            final_k=self.top_k
        )
        
        return {"retrieved_docs": merged_docs}