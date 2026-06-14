from __future__ import annotations

from typing import Any

from app.agents.document_agent import DocumentAgent
from app.agents.mindmap_agent import MindMapAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.practice_agent import PracticeAgent
from app.agents.profile_agent import ProfileAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.safety_agent import SafetyCheckAgent
from app.graph.state import AgentState


def run_sequential_workflow(input_state: dict[str, Any]) -> AgentState:
    state: AgentState = AgentState(**input_state)

    state["profile"] = ProfileAgent().run(state)
    state.update(RetrieverAgent().run(state))
    state.update(PlannerAgent().run(state))
    state.update(DocumentAgent().run(state))
    state.update(MindMapAgent().run(state))
    state.update(QuizAgent().run(state))
    state.update(PracticeAgent().run(state))
    state.update(SafetyCheckAgent().run(state))

    return state
