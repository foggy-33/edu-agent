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

    # Step 1: 学生画像
    state["profile"] = ProfileAgent().run(state)
    
    # Step 2: 知识检索
    state.update(RetrieverAgent().run(state))
    
    # Step 3: 学习路径规划
    state.update(PlannerAgent().run(state))
    
    # Step 4: 生成文档 + 安全检查
    state.update(DocumentAgent().run(state))
    if _check_and_block(state, "document"):
        return state
    
    # Step 5: 生成思维导图 + 安全检查
    state.update(MindMapAgent().run(state))
    if _check_and_block(state, "mindmap"):
        return state
    
    # Step 6: 生成测验 + 安全检查
    state.update(QuizAgent().run(state))
    if _check_and_block(state, "quiz"):
        return state
    
    # Step 7: 生成练习 + 安全检查
    state.update(PracticeAgent().run(state))
    if _check_and_block(state, "practice_case"):
        return state
    
    # Step 8: 最终安全检查
    state.update(SafetyCheckAgent().run(state))

    return state


def _check_and_block(state: AgentState, content_key: str) -> bool:
    """执行安全检查并判断是否需要拦截"""
    agent = SafetyCheckAgent()
    result = agent.run({content_key: state.get(content_key, "")})
    report = result["safety_report"]
    
    if report["status"] == "fail":
        state["safety_blocked"] = True
        state["blocked_by"] = content_key
        state["block_reason"] = report
        return True
    
    return False
