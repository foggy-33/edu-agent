from __future__ import annotations

from typing import Any, TypedDict


class LearningState(TypedDict, total=False):
    major: str
    course: str
    chapter: str
    weakness: str
    goal: str
    resourceTypes: list[str]
    api_key: str
    base_url: str
    model: str
    studentProfile: dict[str, Any]
    taskPlan: list[dict[str, str]]
    lectureDoc: str
    mindmap: str
    exercises: str
    reading: str
    codeCase: str
    videoScript: str
    review: str
    agentTrace: list[dict[str, Any]]
