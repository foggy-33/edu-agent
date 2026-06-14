from __future__ import annotations

from typing import Any


class PlannerAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        profile = state.get("profile", {})
        weak_points = profile.get("weak_points", ["函数依赖", "候选码", "范式判断"])
        path = []
        for index, point in enumerate(weak_points, start=1):
            path.append(
                {
                    "stage": index,
                    "title": f"{point}专项突破",
                    "goal": f"掌握{point}的核心概念、判断步骤与典型题型。",
                    "tasks": [
                        f"阅读{point}知识点讲解",
                        "完成 2 道基础题和 1 道应用题",
                        "整理错题中的判断依据",
                    ],
                    "estimated_time": "45-60 分钟",
                    "recommended_resources": ["讲解文档", "思维导图", "练习题"],
                }
            )
        path.append(
            {
                "stage": len(path) + 1,
                "title": "综合应用与 SQL 实操",
                "goal": "把理论判断迁移到关系表设计和 SQL 查询任务。",
                "tasks": ["完成 SQL 建表与查询练习", "复盘范式设计是否合理"],
                "estimated_time": "60 分钟",
                "recommended_resources": ["SQL案例", "拓展阅读"],
            }
        )
        return {"learning_path": path}
