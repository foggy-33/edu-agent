from __future__ import annotations

from typing import Any

from app.core.config import get_settings


class LLMClient:
    """LLM adapter. Mock mode is the default for local demos and tests."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mode = self.settings.llm_mode.lower()

    def generate(self, prompt: str, task: str = "general", **kwargs: Any) -> str:
        if self.mode == "mock":
            return self.mock_generate(prompt=prompt, task=task, **kwargs)
        if self.mode == "spark":
            return self.spark_generate(prompt=prompt, task=task, **kwargs)
        return self.mock_generate(prompt=prompt, task=task, **kwargs)

    def mock_generate(self, prompt: str, task: str = "general", **kwargs: Any) -> str:
        mock_outputs = {
            "document": (
                "# 个性化课程讲解文档\n\n"
                "## 学习目标\n"
                "围绕函数依赖、候选码与范式判断建立可操作的解题流程。\n\n"
                "## 核心方法\n"
                "1. 先列出关系模式和函数依赖集合。\n"
                "2. 通过属性闭包判断候选码。\n"
                "3. 根据主属性、非主属性和依赖类型判断 2NF、3NF、BCNF。\n\n"
                "## 例题\n"
                "设 R(A,B,C)，F={A->B, B->C}。A+={A,B,C}，因此 A 是候选码。\n"
                "由于 B->C 的左部 B 不是超码，R 不满足 BCNF。\n"
            ),
            "mindmap": (
                "mindmap\n"
                "  root((数据库系统复习))\n"
                "    函数依赖\n"
                "      属性闭包\n"
                "      最小依赖集\n"
                "    候选码\n"
                "      超码\n"
                "      主属性\n"
                "    范式判断\n"
                "      2NF\n"
                "      3NF\n"
                "      BCNF\n"
                "    SQL实操\n"
                "      建表\n"
                "      查询\n"
            ),
            "general": "这是 mock LLM 返回的结构化教学内容。",
        }
        return mock_outputs.get(task, mock_outputs["general"])

    def spark_generate(self, prompt: str, task: str = "general", **kwargs: Any) -> str:
        raise NotImplementedError("Spark API adapter is reserved. Configure keys in .env before implementation.")
