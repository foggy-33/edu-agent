from __future__ import annotations

from typing import Any, Callable

from app.agents.profile_agent import ProfileAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.document_agent import DocumentAgent
from app.agents.mindmap_agent import MindMapAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.practice_agent import PracticeAgent
from app.agents.safety_agent import SafetyCheckAgent
from app.graph.fallback_workflow import run_sequential_workflow
from app.graph.state import AgentState


def _build_langgraph_app() -> Callable[[dict[str, Any]], AgentState] | None:
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None

    graph = StateGraph(AgentState)

    graph.add_node("profile", lambda s: {"profile": ProfileAgent().run(s)})
    graph.add_node("retriever", lambda s: RetrieverAgent().run(s))
    graph.add_node("planner", lambda s: PlannerAgent().run(s))
    graph.add_node("document", lambda s: DocumentAgent().run(s))
    graph.add_node("document_safety", lambda s: _check_document_safety(s))
    graph.add_node("mindmap", lambda s: MindMapAgent().run(s))
    graph.add_node("mindmap_safety", lambda s: _check_mindmap_safety(s))
    graph.add_node("quiz", lambda s: QuizAgent().run(s))
    graph.add_node("quiz_safety", lambda s: _check_quiz_safety(s))
    graph.add_node("practice", lambda s: PracticeAgent().run(s))
    graph.add_node("practice_safety", lambda s: _check_practice_safety(s))
    graph.add_node("final_safety", lambda s: SafetyCheckAgent().run(s))

    graph.set_entry_point("profile")
    graph.add_edge("profile", "retriever")
    graph.add_edge("retriever", "planner")
    graph.add_edge("planner", "document")
    graph.add_edge("document", "document_safety")
    graph.add_conditional_edges("document_safety", _should_continue, {"continue": "mindmap", "block": END})
    graph.add_edge("mindmap", "mindmap_safety")
    graph.add_conditional_edges("mindmap_safety", _should_continue, {"continue": "quiz", "block": END})
    graph.add_edge("quiz", "quiz_safety")
    graph.add_conditional_edges("quiz_safety", _should_continue, {"continue": "practice", "block": END})
    graph.add_edge("practice", "practice_safety")
    graph.add_conditional_edges("practice_safety", _should_continue, {"continue": "final_safety", "block": END})
    graph.add_edge("final_safety", END)

    app = graph.compile()

    def invoke(input_state: dict[str, Any]) -> AgentState:
        state = app.invoke(input_state)
        state["extended_reading"] = _build_extended_reading(state)
        return state

    return invoke


def _check_document_safety(state: dict[str, Any]) -> dict[str, Any]:
    """检查文档内容安全"""
    agent = SafetyCheckAgent()
    result = agent.run({"document": state.get("document", "")})
    report = result["safety_report"]
    if report["status"] == "fail":
        state["safety_blocked"] = True
        state["blocked_by"] = "document"
        state["block_reason"] = report
    return {"safety_check": report}


def _check_mindmap_safety(state: dict[str, Any]) -> dict[str, Any]:
    """检查思维导图内容安全"""
    agent = SafetyCheckAgent()
    result = agent.run({"mindmap": state.get("mindmap", "")})
    report = result["safety_report"]
    if report["status"] == "fail":
        state["safety_blocked"] = True
        state["blocked_by"] = "mindmap"
        state["block_reason"] = report
    return {"safety_check": report}


def _check_quiz_safety(state: dict[str, Any]) -> dict[str, Any]:
    """检查测验内容安全"""
    agent = SafetyCheckAgent()
    result = agent.run({"quiz": state.get("quiz", "")})
    report = result["safety_report"]
    if report["status"] == "fail":
        state["safety_blocked"] = True
        state["blocked_by"] = "quiz"
        state["block_reason"] = report
    return {"safety_check": report}


def _check_practice_safety(state: dict[str, Any]) -> dict[str, Any]:
    """检查练习内容安全"""
    agent = SafetyCheckAgent()
    result = agent.run({"practice_case": state.get("practice_case", "")})
    report = result["safety_report"]
    if report["status"] == "fail":
        state["safety_blocked"] = True
        state["blocked_by"] = "practice_case"
        state["block_reason"] = report
    return {"safety_check": report}


def _should_continue(state: dict[str, Any]) -> str:
    """判断是否继续执行"""
    if state.get("safety_blocked"):
        return "block"
    return "continue"


def _build_extended_reading(state: dict[str, Any]) -> list[dict[str, str]]:
    docs = state.get("retrieved_docs", [])
    readings = [
        {"title": doc.get("title", "数据库系统资料"), "source": doc.get("source", ""), "reason": "与当前薄弱点匹配"}
        for doc in docs[:3]
    ]
    return readings or [
        {"title": "数据库系统基础复习", "source": "knowledge_base/database_system", "reason": "补充课程基础概念"}
    ]


def run_agent_workflow(input_state: dict[str, Any]) -> dict[str, Any]:
    langgraph_app = _build_langgraph_app()
    state = langgraph_app(input_state) if langgraph_app else run_sequential_workflow(input_state)
    state["extended_reading"] = _build_extended_reading(state)
    
    # 检查是否被安全拦截
    if state.get("safety_blocked"):
        return {
            "profile": state.get("profile", {}),
            "learning_path": state.get("learning_path", []),
            "resources": {
                "document": state.get("document", ""),
                "mindmap": state.get("mindmap", ""),
                "quiz": state.get("quiz", []),
                "practice_case": state.get("practice_case", ""),
                "extended_reading": state.get("extended_reading", []),
            },
            "safety_report": {
                "status": "blocked",
                "risk_level": "high",
                "blocked_by": state.get("blocked_by", ""),
                "block_reason": state.get("block_reason", {}),
                "message": "内容生成被安全检查拦截，请根据以下建议修改内容："
            },
        }
    
    return {
        "profile": state.get("profile", {}),
        "learning_path": state.get("learning_path", []),
        "resources": {
            "document": state.get("document", ""),
            "mindmap": state.get("mindmap", ""),
            "quiz": state.get("quiz", []),
            "practice_case": state.get("practice_case", ""),
            "extended_reading": state.get("extended_reading", []),
        },
        "safety_report": state.get("safety_report", {"status": "warning", "notes": ["工作流未生成安全报告"]}),
    }


def workflow_description() -> dict[str, Any]:
    return {
        "name": "个性化资源生成多 Agent 工作流",
        "engine": "LangGraph if installed, otherwise Python sequential fallback",
        "steps": [
            {"order": 1, "agent": "ProfileAgent", "description": "抽取学生画像和学习偏好"},
            {"order": 2, "agent": "RetrieverAgent", "description": "从课程知识库检索相关资料"},
            {"order": 3, "agent": "PlannerAgent", "description": "生成阶段化学习路径"},
            {"order": 4, "agent": "DocumentAgent", "description": "生成 Markdown 个性化讲解文档"},
            {"order": 5, "agent": "MindMapAgent", "description": "生成 Mermaid mindmap"},
            {"order": 6, "agent": "QuizAgent", "description": "生成多题型练习题"},
            {"order": 7, "agent": "PracticeAgent", "description": "生成 SQL 实操案例"},
            {"order": 8, "agent": "SafetyCheckAgent", "description": "检查教学适用性与知识库依据"},
        ],
    }
