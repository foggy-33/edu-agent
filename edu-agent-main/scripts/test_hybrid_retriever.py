#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试混合检索功能 - Windows适配版本"""

import sys
import os

# Windows固定路径 - 无(1)标记
PROJECT_ROOT = r"C:\Users\wyh\Downloads\edu-agent-main\edu-agent-main"

# 设置Python路径
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 切换工作目录
os.chdir(PROJECT_ROOT)

# 导入模块
from app.agents.retriever_agent import RetrieverAgent

print("=" * 60)
print("混合检索测试")
print("=" * 60)
print("Python版本:", sys.version.split()[0])
print("项目目录:", PROJECT_ROOT)
print()

# 创建Agent实例
agent = RetrieverAgent()
print("RetrieverAgent初始化成功")
print()

# 执行检索
print("开始执行检索...")
result = agent.run({
    "message": "什么是数据库的第一范式？",
    "profile": {}
})

# 打印结果
print()
print("检索结果：")
for i, doc in enumerate(result["retrieved_docs"], 1):
    print()
    print("【结果{}】".format(i))
    print("  标题:", doc.get("title", "N/A"))
    print("  来源:", doc.get("source", "N/A"))
    print("  关键词得分:", doc.get("keyword_score", 0))
    print("  向量得分:", doc.get("vector_score") or 0)
    print("  综合得分:", doc.get("combined_score", 0))
    print("  召回来源:", doc.get("retrieval_types", []))
    content = doc.get("content", "")[:150]
    print("  内容预览:", content.replace("\n", " "))