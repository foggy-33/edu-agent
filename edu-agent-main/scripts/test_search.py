#!/usr/bin/env python3
"""测试向量检索功能"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scripts.vector_store import KnowledgeVectorStore

# 初始化向量库（自动加载faiss_index中的持久化索引）
store = KnowledgeVectorStore()

# 测试查询问题
query = "数据库的第一范式是什么？"

# 调用检索接口
results = store.search(query, k=3)

# 打印结果
print(f"查询问题：{query}\n")
print("检索到的相关内容：\n")
for i, doc in enumerate(results, 1):
    print(f"【结果{i}】\n{doc.page_content}\n---")
