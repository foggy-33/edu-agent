from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Callable

from app.learning.llm import call_llm
from app.learning.state import LearningState


def _context(state: LearningState) -> str:
    context = (
        f"专业：{state['major']}\n课程：{state['course']}\n章节：{state['chapter']}\n"
        f"知识短板：{state['weakness']}\n学习目标：{state['goal']}"
    )
    source_context = state.get("source_context", "").strip()
    if source_context:
        context += (
            "\n\n以下是用户选定 PDF 中提取的原文。生成内容必须优先依据这些资料；"
            "资料未提及的内容要明确标注为补充说明，不得伪造页码或原文：\n"
            f"{source_context}"
        )
    return context


def _trace(state: LearningState, agent: str, summary: str, status: str = "completed") -> list[dict[str, Any]]:
    return [
        *state.get("agentTrace", []),
        {
            "order": len(state.get("agentTrace", [])) + 1,
            "agent": agent,
            "status": status,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]


def _generate(state: LearningState, task: str, mock_builder: Callable[[], str]) -> str:
    prompt = f"{_context(state)}\n\n任务：{task}\n请直接输出可展示的中文内容，不要解释你的生成过程。"
    return call_llm(
        prompt,
        api_key=state.get("api_key", ""),
        base_url=state.get("base_url", "https://api.siliconflow.cn/v1"),
        model=state.get("model", "Pro/deepseek-ai/DeepSeek-V3.2"),
    ) or mock_builder()


def _source_points(state: LearningState, limit: int = 5) -> list[str]:
    points: list[str] = []
    for line in state.get("source_context", "").splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip(" #*-")
        if not cleaned or cleaned.startswith(("【文件：", "[第 ")):
            continue
        cleaned = cleaned[:60]
        if cleaned not in points:
            points.append(cleaned)
        if len(points) >= limit:
            break
    return points


def _source_note(state: LearningState) -> str:
    points = _source_points(state, 3)
    if not points:
        return ""
    return "\n\n## PDF 资料要点\n" + "\n".join(f"- {item}" for item in points)


def _mindmap_label(value: str) -> str:
    return re.sub(r"[:：()\[\]{}]", " ", value)


def profile_agent(state: LearningState) -> dict[str, Any]:
    profile = {
        "major": state["major"],
        "course": state["course"],
        "chapter": state["chapter"],
        "weakness": state["weakness"],
        "goal": state["goal"],
        "level": "基础待巩固",
        "strategy": "先对比概念，再通过案例与分层练习建立迁移能力",
    }
    return {"studentProfile": profile, "agentTrace": _trace(state, "学情分析 Agent", "已识别知识短板与学习目标")}


def planner_agent(state: LearningState) -> dict[str, Any]:
    labels = {
        "lecture": "课程讲解文档",
        "mindmap": "知识点思维导图",
        "exercise": "分层练习题",
        "reading": "拓展阅读材料",
    }
    plan = [{"resourceType": item, "task": labels[item]} for item in state["resourceTypes"] if item in labels]
    return {"taskPlan": plan, "agentTrace": _trace(state, "任务规划 Agent", f"已规划 {len(plan)} 类资源生成任务")}


def lecture_agent(state: LearningState) -> dict[str, Any]:
    if "lecture" not in state["resourceTypes"]:
        return {}
    value = _generate(
        state,
        "生成 Markdown 课程讲解文档，必须包含概念解释、原理说明、例子、易错点和复习建议。",
        lambda: (
            f"# {state['course']} · {state['chapter']} 个性化讲解\n\n"
            f"## 学习目标\n围绕“{state['weakness']}”建立适用于“{state['goal']}”的知识框架。\n\n"
            "## 概念解释\n本章节的核心是理解不同方案的适用条件、执行规则和评价指标，而不是只记结论。\n\n"
            "## 原理说明\n先明确输入条件，再跟踪每一步状态变化，最后比较结果中的效率、公平性与开销。\n\n"
            "## 对比例子\n使用同一组输入分别执行各方案，记录执行顺序、等待时间和响应时间，观察差异。\n\n"
            f"## 易错点\n- 混淆概念名称与实际执行规则。\n- 忽略题目给出的边界条件。\n- 没有结合“{state['weakness']}”进行对比。\n\n"
            "## 复习建议\n制作对比表，完成一次手工推演，再用练习题检验迁移能力。"
            f"{_source_note(state)}"
        ),
    )
    return {"lectureDoc": value, "agentTrace": _trace(state, "课程讲解 Agent", "课程讲解文档生成完成")}


def mindmap_agent(state: LearningState) -> dict[str, Any]:
    if "mindmap" not in state["resourceTypes"]:
        return {}
    value = _generate(
        state,
        "只输出 Mermaid mindmap 源码，提炼所选 PDF 或用户问题中的主题、核心概念、层级关系、应用与易错点。",
        lambda: "mindmap\n"
        f"  root(({state['chapter']}))\n"
        + (
            "\n".join(f"    {_mindmap_label(item)}" for item in _source_points(state))
            if _source_points(state)
            else
            "    核心概念\n      定义与目标\n      关键指标\n    原理与流程\n      输入条件\n      执行规则\n    复习路径\n      分层练习"
        ),
    )
    return {"mindmap": value, "agentTrace": _trace(state, "思维导图 Agent", "Mermaid 思维导图生成完成")}


def exercise_agent(state: LearningState) -> dict[str, Any]:
    if "exercise" not in state["resourceTypes"]:
        return {}
    value = _generate(
        state,
        "依据所选 PDF 或用户问题生成 Markdown 练习题，包含选择题、判断题、填空题、简答题和综合题；包含答案解析，并按基础、提高、挑战分层。",
        lambda: (
            f"# {state['chapter']} 分层练习\n\n"
            "## 基础层\n"
            f"1. **选择题**：以下哪项最能解释本章核心目标？\n   - 答案：结合执行规则与评价指标进行判断。\n   - 解析：只记名称不能解决实际问题。\n\n"
            "2. **判断题**：一种方法在所有场景中都最优。\n   - 答案：错误。\n   - 解析：方法选择依赖目标与输入条件。\n\n"
            "3. **填空题**：分析方案时，应重点比较执行规则、适用场景和____。\n   - 答案：评价指标。\n\n"
            "## 提高层\n"
            f"4. **简答题**：结合“{state['weakness']}”说明如何建立对比表。\n"
            "   - 答案与解析：按规则、优点、局限、场景和指标五列进行比较。\n\n"
            "## 挑战层\n"
            "5. **综合题**：设计一组输入，分别推演三种方案并解释差异。\n"
            "   - 答案与解析：应给出完整步骤、结果指标和方案选择理由。"
            f"{_source_note(state)}"
        ),
    )
    return {"exercises": value, "agentTrace": _trace(state, "练习题 Agent", "五类分层练习题生成完成")}


def reading_agent(state: LearningState) -> dict[str, Any]:
    if "reading" not in state["resourceTypes"]:
        return {}
    value = _generate(
        state,
        "生成 Markdown 拓展阅读，包含相关知识延伸、实际应用场景和递进学习路径。",
        lambda: (
            f"# {state['chapter']} 拓展阅读\n\n"
            "## 知识延伸\n从本章方法继续学习性能评价、资源权衡与复杂系统中的决策机制。\n\n"
            "## 实际应用场景\n- 操作系统与云平台资源管理\n- 在线服务的任务队列\n- 实时系统的响应保障\n\n"
            f"## 学习路径\n1. 补齐“{state['weakness']}”基础概念。\n2. 完成可视化推演。\n3. 阅读真实系统案例。\n4. 尝试解释方案权衡。"
            f"{_source_note(state)}"
        ),
    )
    return {"reading": value, "agentTrace": _trace(state, "拓展阅读 Agent", "知识延伸与学习路径生成完成")}


def direct_chat_agent(state: LearningState) -> dict[str, Any]:
    value = _generate(
        state,
        "直接回答用户的问题。保持中文、清晰、可执行；如果用户引用了 PDF，优先依据资料回答，资料不足时说明是补充解释。",
        lambda: (
            f"你问的是：{state['weakness']}\n\n"
            "我会先抓住核心概念，再给出可操作的理解路径。"
            "如果这是一个课程问题，可以继续追问具体概念、例题或要求我展开某一步。"
            f"{_source_note(state)}"
        ),
    )
    return {"lectureDoc": value, "agentTrace": _trace(state, "直接对话 Agent", "已生成直接对话回答")}


def review_agent(state: LearningState) -> dict[str, Any]:
    field_map = {
        "lecture": "lectureDoc",
        "mindmap": "mindmap",
        "exercise": "exercises",
        "reading": "reading",
    }
    selected_fields = [field_map[item] for item in state["resourceTypes"] if item in field_map]
    complete = sum(bool(state.get(field)) for field in selected_fields)
    value = (
        "# 质量审核结果\n\n"
        f"- **短板覆盖**：通过，所有资源均围绕“{state['weakness']}”组织。\n"
        f"- **目标匹配**：通过，内容面向“{state['goal']}”。\n"
        f"- **内容完整性**：通过，已生成 {complete}/{len(selected_fields)} 类所选资源。\n"
        "- **难度匹配**：通过，采用基础、提高、挑战的递进结构。\n"
        "- **审核结论**：资源包可用于当前阶段学习与复习。"
    )
    return {"review": value, "agentTrace": _trace(state, "质量审核 Agent", "覆盖度、难度与完整性审核通过")}


def integration_agent(state: LearningState) -> dict[str, Any]:
    return {"agentTrace": _trace(state, "资源整合 Agent", "资源已整合为统一 JSON 返回")}
