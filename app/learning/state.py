from __future__ import annotations

from typing import Any, TypedDict


class LearningState(TypedDict, total=False):
    major: str
    course: str
    chapter: str
    weakness: str
    goal: str
    resourceTypes: list[str]
    fileIds: list[str]
    source_context: str
    sources: list[dict[str, Any]]
    api_key: str
    base_url: str
    model: str
    active_provider: str
    spark_api_password: str
    spark_base_url: str
    spark_model: str
    studentProfile: dict[str, Any]
    taskPlan: list[dict[str, str]]
    lectureDoc: str
    mindmap: str
    exercises: str
    exerciseItems: list[dict[str, Any]]
    reading: str
    codeCase: str
    learningPath: str
    review: str
    agentTrace: list[dict[str, Any]]
