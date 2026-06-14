from __future__ import annotations

from typing import Any


class SafetyCheckAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        notes: list[str] = []
        if not state.get("retrieved_docs"):
            notes.append("未检索到足够知识库依据，建议补充课程资料后再生成。")
        if state.get("profile", {}).get("course") != "数据库系统":
            notes.append("当前知识库主要覆盖数据库系统，其他课程内容可能依据不足。")
        return {
            "safety_report": {
                "status": "warning" if notes else "pass",
                "notes": notes,
            }
        }
