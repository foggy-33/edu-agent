from __future__ import annotations

from typing import Any

from app.core.llm_client import LLMClient


class MindMapAgent:
    def __init__(self) -> None:
        self.llm = LLMClient()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = state.get("profile", {})
        prompt = f"根据薄弱点 {profile.get('weak_points', [])} 生成 Mermaid mindmap。"
        return {"mindmap": self.llm.generate(prompt, task="mindmap")}
