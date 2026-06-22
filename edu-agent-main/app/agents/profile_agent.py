from __future__ import annotations

import re
from typing import Any


class ProfileAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        message = state.get("message", "")
        course = state.get("course") or "数据库系统"

        weak_points = self._extract_weak_points(message)
        return {
            "major": "计算机科学与技术" if "计算机" in message else "未明确",
            "course": course,
            "grade_level": self._extract_grade(message),
            "learning_goal": "期末复习" if any(word in message for word in ["考试", "复习", "期末"]) else "课程学习",
            "knowledge_level": self._extract_level(message),
            "weak_points": weak_points,
            "learning_style": "步骤化讲解" if any(word in message for word in ["步骤", "例题", "一步"]) else "概念讲解结合练习",
            "resource_preference": self._extract_preferences(message),
        }

    def _extract_grade(self, message: str) -> str:
        for grade in ["大一", "大二", "大三", "大四", "研一", "研二", "研三"]:
            if grade in message:
                return grade
        return "未明确"

    def _extract_level(self, message: str) -> str:
        if re.search(r"不太会|不会|薄弱|困难|看不懂", message):
            return "中等偏弱"
        if re.search(r"基础|刚学|入门", message):
            return "初学"
        if re.search(r"提高|进阶|深入", message):
            return "中等"
        return "中等"

    def _extract_weak_points(self, message: str) -> list[str]:
        candidates = [
            "函数依赖",
            "候选码",
            "范式判断",
            "关系模型",
            "SQL",
            "事务",
            "并发控制",
            "索引",
            "存储管理",
        ]
        found = [item for item in candidates if item in message]
        return found or ["函数依赖", "候选码", "范式判断"]

    def _extract_preferences(self, message: str) -> list[str]:
        mapping = {
            "文档": "讲解文档",
            "讲解": "讲解文档",
            "思维导图": "思维导图",
            "练习": "练习题",
            "题": "练习题",
            "SQL": "SQL案例",
            "案例": "SQL案例",
        }
        prefs: list[str] = []
        for key, value in mapping.items():
            if key in message and value not in prefs:
                prefs.append(value)
        return prefs or ["讲解文档", "思维导图", "练习题", "SQL案例"]
