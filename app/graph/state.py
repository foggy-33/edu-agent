from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_id: str
    course: str
    message: str
    profile: dict[str, Any]
    retrieved_docs: list[dict[str, Any]]
    retrieval_meta: dict[str, Any]
    learning_path: list[dict[str, Any]]
    document: str
    mindmap: str
    quiz: list[dict[str, Any]]
    practice_case: str
    extended_reading: list[dict[str, str]]
    safety_report: dict[str, Any]
