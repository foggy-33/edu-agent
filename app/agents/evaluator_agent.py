from __future__ import annotations

from collections import Counter
from typing import Any


class EvaluatorAgent:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        answers = payload.get("answers", [])
        total = len(answers)
        incorrect = [item for item in answers if item.get("is_correct") is False]
        correct_count = sum(1 for item in answers if item.get("is_correct") is True)
        topic_counter = Counter(item.get("topic") or "综合应用" for item in incorrect)
        weak_points = [topic for topic, _ in topic_counter.most_common()] or ["函数依赖", "候选码"]

        accuracy = round(correct_count / total, 2) if total else None
        return {
            "user_id": payload.get("user_id"),
            "course": payload.get("course", "数据库系统"),
            "score_summary": {
                "total": total,
                "correct": correct_count,
                "incorrect": len(incorrect),
                "accuracy": accuracy,
            },
            "weak_points": weak_points,
            "analysis": "学生在概念辨析和步骤化推理上仍需加强，建议优先复盘错题对应知识点。",
            "next_steps": [
                f"重新学习{weak_points[0]}的概念和例题",
                "用属性闭包或 SQL 查询过程写出完整推导步骤",
                "完成 3 道同类变式题并记录错误原因",
            ],
        }
