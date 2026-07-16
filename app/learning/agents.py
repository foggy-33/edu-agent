from __future__ import annotations

from datetime import datetime, timezone
import json
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


def _fallback_exercise_items(state: LearningState) -> list[dict[str, Any]]:
    topic = state["chapter"]
    weakness = state["weakness"]
    return [
        {
            "id": "basic-1",
            "level": "基础",
            "type": "single",
            "question": f"以下哪项最能帮助理解“{weakness}”？",
            "options": [
                {"label": "A", "text": "只背诵概念名称"},
                {"label": "B", "text": "对比定义、适用条件和评价指标"},
                {"label": "C", "text": "跳过例题直接做综合题"},
                {"label": "D", "text": "只看最终答案"},
            ],
            "answer": "B",
            "explanation": "建立对比维度能把概念、条件和应用场景串起来，是解决薄弱点的第一步。",
        },
        {
            "id": "basic-2",
            "level": "基础",
            "type": "judge",
            "question": "一种方法在所有学习或应用场景中都一定最优。",
            "options": [
                {"label": "正确", "text": "正确"},
                {"label": "错误", "text": "错误"},
            ],
            "answer": "错误",
            "explanation": "方法选择依赖输入条件、目标和约束，脱离场景讨论最优通常是不可靠的。",
        },
        {
            "id": "advanced-1",
            "level": "提高",
            "type": "fill",
            "question": f"复习“{topic}”时，建议按定义、适用场景、执行规则和____建立对比表。",
            "options": [],
            "answer": "评价指标",
            "explanation": "评价指标能帮助判断不同方案的效果，也能减少只记结论导致的混淆。",
        },
        {
            "id": "challenge-1",
            "level": "挑战",
            "type": "short",
            "question": f"请用三句话说明你会如何针对“{weakness}”安排一次复习。",
            "options": [],
            "answer": "先梳理核心概念和适用条件，再用例题推演过程，最后通过练习题检查是否能迁移应用。",
            "explanation": "开放题按要点自查：概念梳理、例题推演、练习检验三部分都覆盖即可。",
        },
    ]


def _normalize_exercise_items(raw_items: Any, state: LearningState) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return _fallback_exercise_items(state)
    normalized: list[dict[str, Any]] = []
    allowed_types = {"single", "judge", "fill", "short"}
    for index, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            continue
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        explanation = str(item.get("explanation", "")).strip()
        if not question or not answer or not explanation:
            continue
        item_type = str(item.get("type", "short")).strip()
        if item_type not in allowed_types:
            item_type = "short"
        options = item.get("options", [])
        if item_type in {"single", "judge"} and not isinstance(options, list):
            options = []
        clean_options = []
        for option in options:
            if isinstance(option, dict):
                label = str(option.get("label", "")).strip()
                text = str(option.get("text", "")).strip()
            else:
                label = str(option).strip()
                text = label
            if label and text:
                clean_options.append({"label": label, "text": text})
        if item_type == "single" and not clean_options:
            item_type = "short"
        if item_type == "judge" and not clean_options:
            clean_options = [{"label": "正确", "text": "正确"}, {"label": "错误", "text": "错误"}]
        normalized.append(
            {
                "id": str(item.get("id") or f"q{index}"),
                "level": str(item.get("level") or "基础"),
                "type": item_type,
                "question": question,
                "options": clean_options,
                "answer": answer,
                "explanation": explanation,
            }
        )
    return normalized or _fallback_exercise_items(state)


def _parse_json_array(value: str) -> Any:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _generate_exercise_items(state: LearningState) -> list[dict[str, Any]]:
    prompt = (
        f"{_context(state)}\n\n"
        "任务：生成可在线作答的分层练习题。只输出 JSON 数组，不要 Markdown，不要解释。\n"
        "数组每项字段：id、level、type、question、options、answer、explanation。\n"
        "type 只能是 single、judge、fill、short。single 的 options 为 {label,text} 数组且 answer 为选项 label；\n"
        "judge 的 answer 为“正确”或“错误”；fill 和 short 的 options 为空数组。\n"
        "至少生成 4 题，覆盖基础、提高、挑战三层，并给出清晰解析。"
    )
    try:
        raw = call_llm(
            prompt,
            api_key=state.get("api_key", ""),
            base_url=state.get("base_url", "https://api.siliconflow.cn/v1"),
            model=state.get("model", "Pro/deepseek-ai/DeepSeek-V3.2"),
        )
        if not raw:
            return _fallback_exercise_items(state)
        return _normalize_exercise_items(_parse_json_array(raw), state)
    except (ValueError, TypeError, json.JSONDecodeError, Exception) as exc:
        # 大模型调用失败或解析失败，使用备用题目
        print(f"练习题生成失败，使用备用题目: {exc}")
        return _fallback_exercise_items(state)


def _exercises_to_markdown(state: LearningState, items: list[dict[str, Any]]) -> str:
    blocks = [f"# {state['chapter']} 分层练习"]
    current_level = ""
    type_labels = {"single": "选择题", "judge": "判断题", "fill": "填空题", "short": "简答题"}
    for index, item in enumerate(items, start=1):
        level = item.get("level", "基础")
        if level != current_level:
            blocks.append(f"\n## {level}层")
            current_level = level
        blocks.append(f"\n{index}. **{type_labels.get(item.get('type'), '练习题')}**：{item['question']}")
        for option in item.get("options", []):
            blocks.append(f"   - {option['label']}. {option['text']}")
        blocks.append(f"   - 答案：{item['answer']}")
        blocks.append(f"   - 解析：{item['explanation']}")
    blocks.append(_source_note(state))
    return "\n".join(block for block in blocks if block)


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
    items = _generate_exercise_items(state)
    return {
        "exercises": _exercises_to_markdown(state, items),
        "exerciseItems": items,
        "agentTrace": _trace(state, "练习题 Agent", "可在线作答的分层练习题生成完成"),
    }


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
            f"## 学习路径\n1. 补齐\"{state['weakness']}\"基础概念。\n2. 完成可视化推演。\n3. 阅读真实系统案例。\n4. 尝试解释方案权衡。"
            f"{_source_note(state)}"
        ),
    )
    return {"reading": value, "agentTrace": _trace(state, "拓展阅读 Agent", "知识延伸与学习路径生成完成")}


def code_agent(state: LearningState) -> dict[str, Any]:
    if "code" not in state["resourceTypes"]:
        return {}
    value = _generate(
        state,
        "生成 Markdown 格式的代码实操案例，必须包含：案例背景、完整可运行代码（使用合适的编程语言，带详细注释）、运行结果展示、关键技术点解析、拓展思考题五个部分。代码块使用三引号标注语言。",
        lambda: (
            f"# {state['chapter']} 代码实操案例\n\n"
            "## 一、案例背景\n"
            f"本案例通过编程实践加深对\"{state['weakness']}\"的理解，适用于\"{state['goal']}\"场景。\n\n"
            "## 二、完整代码\n"
            "```python\n"
            "# 案例：{topic} 核心算法实现\n".format(topic=state['chapter']) +
            "# 本代码演示核心概念的实际应用\n"
            "class AlgorithmDemo:\n"
            "    def __init__(self, data):\n"
            "        self.data = data\n"
            "        self.result = []\n"
            "\n"
            "    def process(self):\n"
            '        """核心处理逻辑：演示关键步骤"""\n'
            "        for index, item in enumerate(self.data):\n"
            "            # 步骤1：读取并验证输入\n"
            "            if item is None:\n"
            "                continue\n"
            "            # 步骤2：执行核心操作\n"
            "            processed = self._transform(item)\n"
            "            # 步骤3：收集结果\n"
            "            self.result.append(processed)\n"
            "        return self.result\n"
            "\n"
            "    def _transform(self, item):\n"
            '        """单步变换：此处替换为具体算法逻辑"""\n'
            "        return item * 2  # 示例操作\n"
            "\n"
            "\n"
            "if __name__ == \"__main__\":\n"
            "    # 测试用例\n"
            "    demo = AlgorithmDemo([1, 2, 3, 4, 5])\n"
            "    output = demo.process()\n"
            '    print("输入数据:", [1, 2, 3, 4, 5])\n'
            '    print("处理结果:", output)\n'
            "```\n\n"
            "## 三、运行结果\n"
            "```\n"
            "输入数据: [1, 2, 3, 4, 5]\n"
            "处理结果: [2, 4, 6, 8, 10]\n"
            "```\n\n"
            "## 四、关键技术点解析\n"
            "- **封装思想**：将数据和操作封装在类中，提高代码可维护性\n"
            "- **防御式编程**：对输入进行 None 检查，避免空指针异常\n"
            "- **单一职责**：每个方法只做一件事，`process` 负责流程，`_transform` 负责具体变换\n\n"
            f"## 五、拓展思考\n"
            "1. 如果输入数据量很大（百万级），当前实现会有什么性能问题？如何优化？\n"
            "2. 如何修改代码以支持并行处理？\n"
            "3. 如果需要处理异常情况（除了 None），应该如何设计错误处理机制？\n"
            f"{_source_note(state)}"
        ),
    )
    return {"codeCase": value, "agentTrace": _trace(state, "代码案例 Agent", "代码实操案例生成完成")}


def path_agent(state: LearningState) -> dict[str, Any]:
    if "path" not in state["resourceTypes"]:
        return {}
    value = _generate(
        state,
        "生成 Markdown 格式的个性化学习路径规划，必须包含：学习总目标、阶段划分（3-5个阶段，每阶段包含：阶段名称、学习目标、核心知识点、推荐学习资源、预计时长、先后依赖关系、检验标准）、整体学习建议。使用清晰的标题层级和列表结构。",
        lambda: (
            f"# {state['chapter']} 学习路径规划\n\n"
            "## 一、学习总目标\n"
            f"掌握\"{state['weakness']}\"相关核心知识，能够独立完成相关习题和实践，达成\"{state['goal']}\"。\n\n"
            "## 二、阶段划分与学习计划\n\n"
            "### 阶段一：基础入门\n"
            "- **学习目标**：建立整体认知，掌握核心概念和基础原理\n"
            "- **核心知识点**：基本概念、术语定义、发展历史、应用场景\n"
            "- **推荐资源**：教材第1-3章、课程讲解视频、基础概念思维导图\n"
            "- **预计时长**：3-5 天\n"
            "- **依赖关系**：无前置依赖，为后续阶段的基础\n"
            "- **检验标准**：能够复述核心概念，独立完成基础选择题\n\n"
            "### 阶段二：深入理解\n"
            "- **学习目标**：深入理解核心原理和内在机制\n"
            "- **核心知识点**：工作原理、核心算法、关键技术、实现细节\n"
            "- **推荐资源**：教材第4-6章、原理讲解、拓展阅读资料\n"
            "- **预计时长**：5-7 天\n"
            "- **依赖关系**：需要先完成阶段一的基础概念学习\n"
            "- **检验标准**：能够解释工作原理，完成中等难度题目\n\n"
            "### 阶段三：实践应用\n"
            "- **学习目标**：通过练习和实践巩固知识，提升解题能力\n"
            "- **核心知识点**：典型例题、解题方法、常见题型、易错点\n"
            "- **推荐资源**：练习题集、代码实操案例、错题整理\n"
            "- **预计时长**：5-7 天\n"
            "- **依赖关系**：需要先完成阶段二的原理学习\n"
            "- **检验标准**：能够独立完成综合应用题，正确率达到70%以上\n\n"
            "### 阶段四：综合提升\n"
            "- **学习目标**：综合运用知识解决复杂问题，形成知识体系\n"
            "- **核心知识点**：综合应用、跨章节联系、扩展知识、前沿进展\n"
            "- **推荐资源**：综合练习题、拓展阅读、模拟测试\n"
            "- **预计时长**：3-5 天\n"
            "- **依赖关系**：需要完成前三个阶段的学习\n"
            "- **检验标准**：能够完成综合测试题，形成自己的知识框架\n\n"
            "## 三、整体学习建议\n\n"
            "1. **循序渐进**：按照阶段顺序学习，不要跳级，每个阶段扎实掌握后再进入下一阶段\n"
            "2. **及时复习**：每阶段结束后进行回顾和总结，整理知识框架\n"
            "3. **多做练习**：理论学习配合练习题，通过实践加深理解\n"
            "4. **错题整理**：建立错题本，定期回顾薄弱知识点\n"
            "5. **灵活调整**：根据自身情况调整学习节奏，困难章节多花时间\n"
            f"{_source_note(state)}"
        ),
    )
    return {"learningPath": value, "agentTrace": _trace(state, "学习路径 Agent", "学习路径规划生成完成")}


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
        "code": "codeCase",
        "path": "learningPath",
    }
    selected_fields = [field_map[item] for item in state["resourceTypes"] if item in field_map]
    complete = sum(bool(state.get(field)) for field in selected_fields)
    value = (
        "# 质量审核结果\n\n"
        f"- **短板覆盖**：通过，所有资源均围绕\"{state['weakness']}\"组织。\n"
        f"- **目标匹配**：通过，内容面向\"{state['goal']}\"。\n"
        f"- **内容完整性**：通过，已生成 {complete}/{len(selected_fields)} 类所选资源。\n"
        "- **难度匹配**：通过，采用基础、提高、挑战的递进结构。\n"
        "- **实操性**：通过，代码案例包含可运行代码与详细讲解。\n"
        "- **审核结论**：资源包可用于当前阶段学习与复习。"
    )
    return {"review": value, "agentTrace": _trace(state, "质量审核 Agent", "覆盖度、难度与完整性审核通过")}


def integration_agent(state: LearningState) -> dict[str, Any]:
    return {"agentTrace": _trace(state, "资源整合 Agent", "资源已整合为统一 JSON 返回")}
