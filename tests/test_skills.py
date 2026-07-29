import pytest
from pydantic import ValidationError

from app.api.schemas import CollaborativeLearningRequest
from app.learning.agents import _context
from app.learning.state import LearningState


def test_skill_instructions_are_added_to_generation_context() -> None:
    context = _context(LearningState(
        major="计算机科学",
        course="数据库系统",
        chapter="关系模型",
        weakness="关系代数",
        goal="掌握核心概念",
        skill_names=["苏格拉底导师"],
        skill_instructions="先通过递进问题引导学习者思考。",
    ))

    assert "用户已启用以下 Skill：苏格拉底导师" in context
    assert "<skill_instructions>" in context
    assert "先通过递进问题引导学习者思考。" in context


def test_skill_instruction_length_is_limited() -> None:
    with pytest.raises(ValidationError):
        CollaborativeLearningRequest(
            major="计算机科学",
            course="数据库系统",
            chapter="关系模型",
            weakness="关系代数",
            goal="掌握核心概念",
            resourceTypes=[],
            skill_instructions="x" * 20001,
        )
