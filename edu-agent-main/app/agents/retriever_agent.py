from __future__ import annotations

from typing import Any

from app.rag.retriever import KeywordRetriever
from app.rag.vector_store import get_vector_store


class RetrieverAgent:
    """混合检索Agent：关键词检索 + FAISS向量检索融合

    融合策略：
    1. 双路召回：关键词检索(top_k) + 向量检索(top_k)
    2. 去重：根据文档source路径去重
    3. 融合排序：综合得分 = 关键词得分(归一化) * 0.4 + 向量相似度得分(归一化) * 0.6
    4. 输出：统一格式的文档片段列表，包含content、source、score、type(召回来源)
    """

    def __init__(self, top_k: int = 5) -> None:
        """初始化混合检索Agent
        
        Args:
            top_k: 最终返回的文档数量
        """
        self.keyword_retriever = KeywordRetriever()
        self.top_k = top_k

    def _normalize_score(self, score: float, min_score: float, max_score: float) -> float:
        """将分数归一化到[0,1]区间
        
        Args:
            score: 原始分数
            min_score: 最小分数
            max_score: 最大分数
            
        Returns:
            归一化后的分数
        """
        if max_score == min_score:
            return 1.0
        return (score - min_score) / (max_score - min_score)

    def _rerank_and_merge(
        self,
        keyword_results: list[dict],
        vector_results: list[dict],
        final_k: int = 5
    ) -> list[dict]:
        """去重并融合排序双路检索结果
        
        融合公式：综合得分 = 关键词得分(归一化) * 0.4 + 向量相似度得分(归一化) * 0.6
        
        Args:
            keyword_results: 关键词检索结果
            vector_results: 向量检索结果  
            final_k: 最终返回数量
            
        Returns:
            融合排序后的文档列表
        """
        # 建立去重字典，key为source路径
        doc_map: dict[str, dict] = {}
        
        # 处理关键词检索结果
        if keyword_results:
            kw_min = min(d.get("score", 0) for d in keyword_results)
            kw_max = max(d.get("score", 0) for d in keyword_results)
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
        
        # 处理向量检索结果
        if vector_results:
            vec_min = min(d.get("score", 0) for d in vector_results)
            vec_max = max(d.get("score", 0) for d in vector_results)
            for doc in vector_results:
                source = doc.get("source", "")
                if source not in doc_map:
                    doc_map[source] = {
                        "content": doc.get("content", ""),
                        "source": source,
                        "title": doc.get("title", "") or self._extract_title(doc.get("content", "")),
                        "keyword_score": 0,
                        "keyword_score_norm": 0.0,
                        "vector_score": doc.get("score", 0),
                        "vector_score_norm": self._normalize_score(doc.get("score", 0), vec_min, vec_max),
                        "types": ["vector"],
                    }
                else:
                    # 更新向量得分
                    doc_map[source]["vector_score"] = doc.get("score", 0)
                    doc_map[source]["vector_score_norm"] = self._normalize_score(doc.get("score", 0), vec_min, vec_max)
                    doc_map[source]["types"].append("vector")
        
        # 计算综合得分并排序
        # 权重：关键词0.4，向量0.6（向量语义匹配更重要）
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
                "retrieval_types": list(set(doc["types"])),  # 去重
            })
        
        # 按综合得分降序排序
        merged.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return merged[:final_k]

    def _extract_title(self, content: str) -> str:
        """从内容中提取标题（第一行）"""
        if not content:
            return ""
        lines = content.strip().split("\n")
        first_line = lines[0] if lines else ""
        # 移除 Markdown 标题符号
        return first_line.lstrip("# ").strip()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行混合检索
        
        Args:
            state: 工作流状态，包含:
                - message: 用户查询消息
                - profile: 用户画像（含weak_points等）
                
        Returns:
            包含retrieved_docs的字典
        """
        # 提取查询词
        profile = state.get("profile", {})
        query = state.get("message", "")
        
        # 如果有薄弱点信息，加入查询
        weak_points = profile.get("weak_points", [])
        if weak_points:
            query = f"{query} {' '.join(weak_points)}"
        
        # 双路召回数量（最终会融合去重）
        recall_k = self.top_k * 2
        
        # 第一路：关键词检索
        keyword_docs = self.keyword_retriever.search(query, top_k=recall_k)
        print(f"[RetrieverAgent] 关键词检索返回 {len(keyword_docs)} 条结果")
        
        # 第二路：FAISS向量检索
        vector_docs = []
        try:
            vector_store = get_vector_store()
            vector_results = vector_store.similarity_search(query, top_k=recall_k)
            # 转换为统一格式
            for result in vector_results:
                vector_docs.append({
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "score": result.get("score", 0.0),
                    "title": result.get("metadata", {}).get("title", ""),
                })
            print(f"[RetrieverAgent] 向量检索返回 {len(vector_docs)} 条结果")
        except Exception as e:
            print(f"[RetrieverAgent] 向量检索失败: {e}，仅使用关键词检索结果")
        
        # 去重融合排序
        merged_docs = self._rerank_and_merge(
            keyword_results=keyword_docs,
            vector_results=vector_docs,
            final_k=self.top_k
        )
        print(f"[RetrieverAgent] 融合后返回 {len(merged_docs)} 条结果")
        
        return {"retrieved_docs": merged_docs}
