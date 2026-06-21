from __future__ import annotations

from typing import Any, Callable

from app.learning.agents import (
    exercise_agent,
    integration_agent,
    lecture_agent,
    mindmap_agent,
    planner_agent,
    profile_agent,
    reading_agent,
    review_agent,
)
from app.learning.state import LearningState

NODES: list[tuple[str, Callable[[LearningState], dict[str, Any]]]] = [
    ("profile", profile_agent),
    ("planner", planner_agent),
    ("lecture", lecture_agent),
    ("mindmap", mindmap_agent),
    ("exercise", exercise_agent),
    ("reading", reading_agent),
    ("review", review_agent),
    ("integration", integration_agent),
]


def _build_graph() -> Any | None:
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None
    graph = StateGraph(LearningState)
    for name, node in NODES:
        graph.add_node(name, node)
    graph.set_entry_point(NODES[0][0])
    for (current, _), (following, _) in zip(NODES, NODES[1:]):
        graph.add_edge(current, following)
    graph.add_edge(NODES[-1][0], END)
    return graph.compile()


def _run_sequential(state: LearningState) -> LearningState:
    for _, node in NODES:
        state.update(node(state))
    return state


def generate_learning_resources(payload: dict[str, Any]) -> dict[str, Any]:
    initial = LearningState(**payload, agentTrace=[])
    graph = _build_graph()
    state = graph.invoke(initial) if graph else _run_sequential(initial)
    return {
        "lectureDoc": state.get("lectureDoc", ""),
        "mindmap": state.get("mindmap", ""),
        "exercises": state.get("exercises", ""),
        "reading": state.get("reading", ""),
        "review": state.get("review", ""),
        "agentTrace": state.get("agentTrace", []),
    }
