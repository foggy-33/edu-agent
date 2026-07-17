from __future__ import annotations

from typing import Any

from app.core.llm_client import LLMClient


class DocumentAgent:
    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = state.get("profile", {})
        docs = state.get("retrieved_docs", [])
        prompt = f"为学生画像 {profile} 基于资料 {docs[:2]} 生成数据库系统讲解文档。"
        document = self.llm.generate(prompt, task="document")
        return {"document": document}
