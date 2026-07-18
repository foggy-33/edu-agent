import json
import re
from collections import Counter
from typing import Any, Iterator

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.api.schemas import (
    CollaborativeLearningRequest,
    CoursePdfAnnotationRequest,
    EvaluateRequest,
    LearningRequest,
    LoginRequest,
    OnboardingProfileRequest,
    ProfileChatRequest,
    ProfileInterviewRequest,
    QuizAnswerRequest,
    QuizQuestion,
    RegisterRequest,
    SaveGeneratedResourceRequest,
    SiliconFlowConfig,
    SmartEvaluateRequest,
    UpdateResourceFolderRequest,
    UpdateUserProfileRequest,
)
from app.auth.service import AuthError, AuthService
from app.courses.materials import CourseMaterialError, CourseMaterialService
from app.learning.agents import (
    _context,
    _exercises_to_markdown,
    _generate_exercise_items,
    _mindmap_label,
    _source_note,
    _source_points,
    _trace,
    code_agent,
    integration_agent,
    planner_agent,
    profile_agent,
    review_agent,
)
from app.learning.workflow import NODES
from app.learning.llm import stream_llm
from app.learning.state import LearningState
from app.learning.workflow import generate_learning_resources
from app.profiles.service import DynamicProfileService
from app.resources.service import ResourceError, ResourceService

router = APIRouter()
profile_service = DynamicProfileService()
auth_service = AuthService()
resource_service = ResourceService()
course_material_service = CourseMaterialService()


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    return authorization.removeprefix("Bearer ").strip()


def _collaborative_payload(request: CollaborativeLearningRequest) -> dict[str, Any]:
    payload = request.model_dump()
    # 使用 RAG 检索构建上下文
    query = f"{request.course} {request.chapter} {request.weakness} {request.goal}"
    source_context, sources = resource_service.build_context_with_rag(
        request.user_id, 
        request.fileIds, 
        query=query,
        max_chars=2000,
    )
    payload["source_context"] = source_context
    payload["sources"] = sources
    return payload


def _basic_profile(course: str, message: str) -> dict[str, Any]:
    weak_candidates = [
        "函数依赖", "候选码", "范式判断", "关系模型", "SQL", "事务", "并发控制", "索引",
        "存储管理", "数据结构", "算法", "进程调度", "内存管理", "计算机网络", "软件工程",
    ]
    weak_points = [item for item in weak_candidates if item in message] or ["需要通过后续学习行为进一步识别"]
    preferences = []
    preference_map = {
        "文档": "讲解文档",
        "讲解": "讲解文档",
        "思维导图": "思维导图",
        "练习": "练习题",
        "题": "练习题",
        "案例": "案例实践",
        "视频": "教学视频",
    }
    for key, value in preference_map.items():
        if key in message and value not in preferences:
            preferences.append(value)
    grade_level = next((grade for grade in ["大一", "大二", "大三", "大四", "研一", "研二", "研三"] if grade in message), "未明确")
    return {
        "major": "计算机科学与技术" if "计算机" in message else "未明确",
        "course": course,
        "grade_level": grade_level,
        "learning_goal": "考试复习" if any(word in message for word in ["考试", "复习", "期末"]) else "课程学习",
        "knowledge_level": "中等偏弱" if re.search(r"不太会|不会|薄弱|困难|看不懂", message) else "中等",
        "weak_points": weak_points,
        "learning_style": "步骤化讲解" if any(word in message for word in ["步骤", "例题", "一步"]) else "概念讲解结合练习",
        "resource_preference": preferences or ["讲解文档", "练习题"],
    }


def _legacy_generate_response(request: LearningRequest) -> dict[str, Any]:
    profile = _basic_profile(request.course, request.message)
    result = generate_learning_resources(
        {
            "user_id": request.user_id,
            "major": profile["major"],
            "course": request.course,
            "chapter": request.course,
            "weakness": request.message,
            "goal": profile["learning_goal"],
            "resourceTypes": ["lecture", "mindmap", "exercise", "reading"],
            "fileIds": [],
            "sources": [],
            "source_context": "",
            "api_key": "",
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "Pro/deepseek-ai/DeepSeek-V3.2",
        }
    )
    return {
        "profile": profile,
        "learning_path": [
            {
                "stage": item.get("order", index + 1),
                "title": item.get("agent", "协作节点"),
                "goal": item.get("summary", ""),
                "tasks": [item.get("summary", "")],
                "estimated_time": "按需学习",
                "recommended_resources": profile["resource_preference"],
            }
            for index, item in enumerate(result.get("agentTrace", []))
        ],
        "resources": {
            "document": result.get("lectureDoc", ""),
            "mindmap": result.get("mindmap", ""),
            "quiz": result.get("exerciseItems", []),
            "practice_case": "CREATE TABLE learning_note (id INTEGER PRIMARY KEY, topic TEXT, summary TEXT);\n\n"
            + result.get("reading", ""),
            "extended_reading": result.get("sources", []),
        },
        "retrieval_meta": {"source": "app.learning.workflow", "sources": result.get("sources", [])},
        "safety_report": {"status": "pass", "notes": [result.get("review", "已由质量审核 Agent 检查")]},
    }


def _evaluate_answers(payload: dict[str, Any]) -> dict[str, Any]:
    answers = payload.get("answers", [])
    total = len(answers)
    incorrect = [item for item in answers if item.get("is_correct") is False]
    correct_count = sum(1 for item in answers if item.get("is_correct") is True)
    topic_counter = Counter(item.get("topic") or "综合应用" for item in incorrect)
    weak_points = [topic for topic, _ in topic_counter.most_common()] or ["函数依赖", "候选码"]
    accuracy = round(correct_count / total, 2) if total else None
    return {
        "user_id": payload.get("user_id"),
        "course": payload.get("course", "数据库系统"),
        "score_summary": {
            "total": total,
            "correct": correct_count,
            "incorrect": len(incorrect),
            "accuracy": accuracy,
        },
        "weak_points": weak_points,
        "analysis": "学生在概念辨析和步骤化推理上仍需加强，建议优先复盘错题对应知识点。",
        "next_steps": [
            f"重新学习{weak_points[0]}的概念和例题",
            "写出完整推导步骤，避免只记结论",
            "完成同类变式题并记录错误原因",
        ],
    }


def _workflow_description() -> dict[str, Any]:
    return {
        "name": "个性化资源生成多 Agent 工作流",
        "engine": "app.learning.workflow: LangGraph if installed, otherwise Python sequential fallback",
        "steps": [
            {"order": index + 1, "node": name, "description": node.__name__}
            for index, (name, node) in enumerate(NODES)
        ],
    }


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _stream_text(key: str, value: str, size: int = 28) -> Iterator[str]:
    for index in range(0, len(value), size):
        yield _sse("content", {"key": key, "text": value[index:index + size]})


def _generation_prompt(state: LearningState, task: str) -> str:
    return f"{_context(state)}\n\n任务：{task}\n请直接输出可展示的中文内容，不要解释你的生成过程。"


def _stream_generated_text(state: LearningState, key: str, task: str, fallback: str) -> Iterator[str]:
    collected: list[str] = []
    for chunk in stream_llm(
        _generation_prompt(state, task),
        api_key=state.get("api_key", ""),
        base_url=state.get("base_url", "https://api.siliconflow.cn/v1"),
        model=state.get("model", "Pro/deepseek-ai/DeepSeek-V3.2"),
        active_provider=state.get("active_provider", "siliconflow"),
        spark_api_password=state.get("spark_api_password", ""),
        spark_base_url=state.get("spark_base_url", "https://spark-api-open.xf-yun.com/x2"),
        spark_model=state.get("spark_model", "spark-x"),
        response_speed=state.get("response_speed", "balanced"),
    ):
        if chunk["type"] == "reasoning":
            yield _sse("reasoning", {"key": key, "text": chunk["text"]})
            continue
        collected.append(chunk["text"])
        yield _sse("content", {"key": key, "text": chunk["text"]})

    text = "".join(collected).strip()
    if text:
        return text

    yield from _stream_text(key, fallback)
    return fallback


def _lecture_fallback(state: LearningState) -> str:
    return (
        f"# {state['course']} · {state['chapter']} 个性化讲解\n\n"
        f"## 学习目标\n围绕“{state['weakness']}”建立适用于“{state['goal']}”的知识框架。\n\n"
        "## 概念解释\n本章节的核心是理解不同方案的适用条件、执行规则和评价指标，而不是只记结论。\n\n"
        "## 原理说明\n先明确输入条件，再跟踪每一步状态变化，最后比较结果中的效率、公平性与开销。\n\n"
        "## 对比例子\n使用同一组输入分别执行各方案，记录执行顺序、等待时间和响应时间，观察差异。\n\n"
        f"## 易错点\n- 混淆概念名称与实际执行规则。\n- 忽略题目给出的边界条件。\n- 没有结合“{state['weakness']}”进行对比。\n\n"
        "## 复习建议\n制作对比表，完成一次手工推演，再用练习题检验迁移能力。"
        f"{_source_note(state)}"
    )


def _mindmap_fallback(state: LearningState) -> str:
    points = _source_points(state)
    branches = "\n".join(f"    {_mindmap_label(item)}" for item in points)
    if not branches:
        branches = (
            "    核心概念\n"
            "      定义与目标\n"
            "      关键指标\n"
            "    原理与流程\n"
            "      输入条件\n"
            "      执行规则\n"
            "    复习路径\n"
            "      分层练习"
        )
    return f"mindmap\n  root(({state['chapter']}))\n{branches}"


def _reading_fallback(state: LearningState) -> str:
    return (
        f"# {state['chapter']} 拓展阅读\n\n"
        "## 知识延伸\n从本章方法继续学习性能评价、资源权衡与复杂系统中的决策机制。\n\n"
        "## 实际应用场景\n- 操作系统与云平台资源管理\n- 在线服务的任务队列\n- 实时系统的响应保障\n\n"
        f"## 学习路径\n1. 补齐“{state['weakness']}”基础概念。\n2. 完成可视化推演。\n3. 阅读真实系统案例。\n4. 尝试解释方案权衡。"
        f"{_source_note(state)}"
    )


def _code_fallback(state: LearningState) -> str:
    topic = state['chapter']
    weakness = state['weakness']
    goal = state['goal']
    code = (
        f"# {topic} 代码实操案例\n\n"
        "## 一、案例背景\n"
        f"本案例通过编程实践加深对\"{weakness}\"的理解，适用于\"{goal}\"场景。\n\n"
        "## 二、完整代码\n"
        "```python\n"
        f"# 案例：{topic} 核心算法实现\n"
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
        'if __name__ == "__main__":\n'
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
        "## 五、拓展思考\n"
        "1. 如果输入数据量很大（百万级），当前实现会有什么性能问题？如何优化？\n"
        "2. 如何修改代码以支持并行处理？\n"
        "3. 如果需要处理异常情况（除了 None），应该如何设计错误处理机制？\n"
        f"{_source_note(state)}"
    )
    return code


def _path_fallback(state: LearningState) -> str:
    return (
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
    )


def _direct_chat_fallback(state: LearningState) -> str:
    return (
        f"你问的是：{state['weakness']}\n\n"
        "我会先抓住核心概念，再给出可操作的理解路径。"
        "如果这是一个课程问题，可以继续追问具体概念、例题或要求我展开某一步。"
        f"{_source_note(state)}"
    )


def _learning_result(state: LearningState) -> dict[str, Any]:
    return {
        "lectureDoc": state.get("lectureDoc", ""),
        "mindmap": state.get("mindmap", ""),
        "exercises": state.get("exercises", ""),
        "exerciseItems": state.get("exerciseItems", []),
        "reading": state.get("reading", ""),
        "codeCase": state.get("codeCase", ""),
        "learningPath": state.get("learningPath", ""),
        "review": state.get("review", ""),
        "sources": state.get("sources", []),
        "agentTrace": state.get("agentTrace", []),
    }


@router.post("/auth/register", status_code=201)
def register(request: RegisterRequest) -> dict:
    try:
        return auth_service.register(**request.model_dump())
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/login")
def login(request: LoginRequest) -> dict:
    try:
        return auth_service.login(**request.model_dump())
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/auth/me")
def current_user(authorization: str | None = Header(default=None)) -> dict:
    try:
        return {"user": auth_service.authenticate(bearer_token(authorization))}
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/auth/logout", status_code=204)
def logout(authorization: str | None = Header(default=None)) -> None:
    auth_service.logout(bearer_token(authorization))


@router.get("/auth/onboarding")
def get_onboarding_status(authorization: str | None = Header(default=None)) -> dict:
    try:
        user = auth_service.authenticate(bearer_token(authorization))
        return auth_service.get_onboarding_status(user["username"])
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/auth/onboarding")
def save_onboarding_profile(
    request: OnboardingProfileRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    try:
        user = auth_service.authenticate(bearer_token(authorization))
        profile_data = request.model_dump()
        result = auth_service.save_onboarding_profile(user["username"], profile_data)
        profile_service.initialize_from_onboarding(user["username"], profile_data)
        return result
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/auth/profile")
def get_user_profile(authorization: str | None = Header(default=None)) -> dict:
    try:
        user = auth_service.authenticate(bearer_token(authorization))
        return auth_service.get_profile(user["username"])
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.put("/auth/profile")
def update_user_profile(
    request: UpdateUserProfileRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    try:
        user = auth_service.authenticate(bearer_token(authorization))
        result = auth_service.update_profile(user["username"], request.model_dump())
        return {"user": result, "message": "资料更新成功"}
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/analyze")
def analyze(request: LearningRequest) -> dict:
    return {"profile": _basic_profile(request.course, request.message)}


@router.post("/generate")
def generate(request: LearningRequest) -> dict:
    return _legacy_generate_response(request)


@router.post("/learning/generate")
def generate_collaborative_learning_resources(request: CollaborativeLearningRequest) -> dict:
    try:
        return generate_learning_resources(_collaborative_payload(request))
    except ResourceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/learning/generate/stream")
def stream_collaborative_learning_resources(request: CollaborativeLearningRequest) -> StreamingResponse:
    def events() -> Iterator[str]:
        try:
            yield _sse("status", {
                "message": "读取用户问题与资源选择",
                "agent": "请求接入",
                "detail": "接收问题、资源类型、PDF 文件 ID 和模型配置",
                "state": "running",
            })
            payload = _collaborative_payload(request)
            state = LearningState(**payload, agentTrace=[])
            if payload.get("source_context"):
                yield _sse("status", {
                    "message": "PDF 上下文整理完成",
                    "agent": "资料检索",
                    "detail": "读取已选 PDF 的解析文本，拼接为 source_context 供后续 Agent 使用",
                    "state": "done",
                })
            else:
                yield _sse("status", {
                    "message": "未选择 PDF 资料",
                    "agent": "资料检索",
                    "detail": "后续 Agent 将直接围绕用户问题和学习目标生成内容",
                    "state": "done",
                })

            if not request.resourceTypes:
                yield _sse("status", {
                    "message": "直接对话模式启动",
                    "agent": "直接对话 Agent",
                    "detail": "未选择生成内容，跳过资源规划链路，直接组织回答",
                    "state": "running",
                })
                state["lectureDoc"] = yield from _stream_generated_text(
                    state,
                    "lectureDoc",
                    "直接回答用户的问题。保持中文、清晰、可执行；如果用户引用了 PDF，优先依据资料回答，资料不足时说明是补充解释。",
                    _direct_chat_fallback(state),
                )
                state["agentTrace"] = _trace(state, "直接对话 Agent", "已生成直接对话回答")
                yield _sse("status", {
                    "message": "直接对话回答完成",
                    "agent": "直接对话 Agent",
                    "detail": "回答已写入 lectureDoc，并准备保存为历史记录",
                    "state": "done",
                })
                yield _sse("done", {"result": _learning_result(state)})
                return

            yield _sse("status", {
                "message": f"调度 {len(request.resourceTypes)} 类资源生成任务",
                "agent": "协作调度",
                "detail": "按所选资源类型组织学情分析、任务规划、内容生成、质量审核和资源整合",
                "state": "running",
            })

            for node in (profile_agent, planner_agent):
                state.update(node(state))
                trace = state.get("agentTrace", [])[-1]
                yield _sse("status", {
                    "message": trace.get("summary", ""),
                    "agent": trace.get("agent", ""),
                    "detail": "更新共享状态，后续 Agent 将读取该阶段输出继续生成",
                    "state": "done",
                })

            if "lecture" in request.resourceTypes:
                yield _sse("status", {
                    "message": "流式生成课程讲解",
                    "agent": "课程讲解 Agent",
                    "detail": "根据学情、目标和资料上下文生成 Markdown 讲义，并逐段输出",
                    "state": "running",
                })
                state["lectureDoc"] = yield from _stream_generated_text(
                    state,
                    "lectureDoc",
                    "生成 Markdown 课程讲解文档，必须包含概念解释、原理说明、例子、易错点和复习建议。",
                    _lecture_fallback(state),
                )
                state["agentTrace"] = _trace(state, "课程讲解 Agent", "课程讲解文档生成完成")
                yield _sse("status", {
                    "message": "课程讲解文档生成完成",
                    "agent": "课程讲解 Agent",
                    "detail": "讲义内容已写入 lectureDoc",
                    "state": "done",
                })

            if "mindmap" in request.resourceTypes:
                yield _sse("status", {
                    "message": "流式生成思维导图",
                    "agent": "思维导图 Agent",
                    "detail": "提炼主题、概念层级和易错点，输出 Mermaid mindmap 源码",
                    "state": "running",
                })
                state["mindmap"] = yield from _stream_generated_text(
                    state,
                    "mindmap",
                    "只输出 Mermaid mindmap 源码，提炼所选 PDF 或用户问题中的主题、核心概念、层级关系、应用与易错点。",
                    _mindmap_fallback(state),
                )
                state["agentTrace"] = _trace(state, "思维导图 Agent", "Mermaid 思维导图生成完成")
                yield _sse("status", {
                    "message": "Mermaid 思维导图生成完成",
                    "agent": "思维导图 Agent",
                    "detail": "导图源码已写入 mindmap，可在前端渲染",
                    "state": "done",
                })

            if "exercise" in request.resourceTypes:
                yield _sse("status", {
                    "message": "生成可作答分层练习题",
                    "agent": "练习题 Agent",
                    "detail": "生成结构化题目 JSON，再转换为可提交、可判题的练习卡片",
                    "state": "running",
                })
                items = _generate_exercise_items(state)
                state["exerciseItems"] = items
                state["exercises"] = _exercises_to_markdown(state, items)
                state["agentTrace"] = _trace(state, "练习题 Agent", "可在线作答的分层练习题生成完成")
                yield from _stream_text("exercises", state["exercises"])
                yield _sse("status", {
                    "message": "可在线作答的分层练习题生成完成",
                    "agent": "练习题 Agent",
                    "detail": "题目、答案和解析已写入 exerciseItems",
                    "state": "done",
                })

            if "reading" in request.resourceTypes:
                yield _sse("status", {
                    "message": "流式生成拓展阅读",
                    "agent": "拓展阅读 Agent",
                    "detail": "扩展相关知识、应用场景和递进学习路径，并逐段输出",
                    "state": "running",
                })
                state["reading"] = yield from _stream_generated_text(
                    state,
                    "reading",
                    "生成 Markdown 拓展阅读，包含相关知识延伸、实际应用场景和递进学习路径。",
                    _reading_fallback(state),
                )
                state["agentTrace"] = _trace(state, "拓展阅读 Agent", "知识延伸与学习路径生成完成")
                yield _sse("status", {
                    "message": "知识延伸与学习路径生成完成",
                    "agent": "拓展阅读 Agent",
                    "detail": "拓展阅读已写入 reading",
                    "state": "done",
                })

            if "code" in request.resourceTypes:
                yield _sse("status", {
                    "message": "流式生成代码实操案例",
                    "agent": "代码案例 Agent",
                    "detail": "生成包含完整代码、运行结果和讲解的实操案例，并逐段输出",
                    "state": "running",
                })
                state["codeCase"] = yield from _stream_generated_text(
                    state,
                    "codeCase",
                    "生成 Markdown 格式的代码实操案例，必须包含：案例背景、完整可运行代码（使用合适的编程语言，带详细注释）、运行结果展示、关键技术点解析、拓展思考题五个部分。代码块使用三引号标注语言。",
                    _code_fallback(state),
                )
                state["agentTrace"] = _trace(state, "代码案例 Agent", "代码实操案例生成完成")
                yield _sse("status", {
                    "message": "代码实操案例生成完成",
                    "agent": "代码案例 Agent",
                    "detail": "代码案例已写入 codeCase",
                    "state": "done",
                })

            if "path" in request.resourceTypes:
                yield _sse("status", {
                    "message": "流式生成学习路径规划",
                    "agent": "学习路径 Agent",
                    "detail": "生成阶段划分、目标、资源、时长和依赖关系的学习路径，并逐段输出",
                    "state": "running",
                })
                state["learningPath"] = yield from _stream_generated_text(
                    state,
                    "learningPath",
                    "生成 Markdown 格式的个性化学习路径规划，必须包含：学习总目标、阶段划分（3-5个阶段，每阶段包含：阶段名称、学习目标、核心知识点、推荐学习资源、预计时长、先后依赖关系、检验标准）、整体学习建议。使用清晰的标题层级和列表结构。",
                    _path_fallback(state),
                )
                state["agentTrace"] = _trace(state, "学习路径 Agent", "学习路径规划生成完成")
                yield _sse("status", {
                    "message": "学习路径规划生成完成",
                    "agent": "学习路径 Agent",
                    "detail": "学习路径已写入 learningPath",
                    "state": "done",
                })

            yield _sse("status", {
                "message": "执行质量审核",
                "agent": "质量审核 Agent",
                "detail": "检查资源是否覆盖短板、学习目标、完整性和难度匹配",
                "state": "running",
            })
            state.update(review_agent(state))
            yield from _stream_text("review", state.get("review", ""))
            trace = state.get("agentTrace", [])[-1]
            yield _sse("status", {
                "message": trace.get("summary", ""),
                "agent": trace.get("agent", ""),
                "detail": "审核结果已写入 review",
                "state": "done",
            })

            state.update(integration_agent(state))
            trace = state.get("agentTrace", [])[-1]
            yield _sse("status", {
                "message": trace.get("summary", ""),
                "agent": trace.get("agent", ""),
                "detail": "合并讲义、导图、练习、阅读、审核与引用来源，返回统一结果",
                "state": "done",
            })
            yield _sse("done", {"result": _learning_result(state)})
        except ResourceError as exc:
            yield _sse("error", {"message": str(exc)})
        except ValueError as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/resources/upload", status_code=201)
def upload_resource(
    user_id: str = Form(...),
    course_folder: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="仅支持上传 PDF 文件")
    try:
        return {
            "resource": resource_service.upload_pdf(
                user_id=user_id,
                filename=file.filename or "document.pdf",
                stream=file.file,
                course_folder=course_folder,
            )
        }
    except ResourceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        file.file.close()


@router.get("/resources")
def list_resources(user_id: str) -> dict:
    return {"resources": resource_service.list_resources(user_id)}


@router.get("/resources/{file_id}/download")
def download_resource(file_id: str, user_id: str) -> FileResponse:
    try:
        metadata = resource_service.get_metadata(user_id, file_id)
        resource_type = metadata.get("type", "pdf")
        if resource_type == "pdf":
            path = resource_service.get_pdf_path(user_id, file_id)
            media_type = "application/pdf"
            filename = metadata["name"]
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
        else:
            path = resource_service.get_content_path(user_id, file_id)
            media_type = "text/markdown; charset=utf-8"
            ext_map = {
                "markdown": ".md",
                "mindmap": ".mmd",
                "lecture": ".md",
                "review": ".md",
                "reading": ".md",
                "exercises": ".md",
            }
            ext = ext_map.get(resource_type, ".txt")
            filename = metadata["name"] + ext
        return FileResponse(path, media_type=media_type, filename=filename)
    except ResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/resources/{file_id}/preview")
def preview_resource(file_id: str, user_id: str) -> FileResponse:
    try:
        metadata = resource_service.get_metadata(user_id, file_id)
        resource_type = metadata.get("type", "pdf")
        if resource_type == "pdf":
            path = resource_service.get_pdf_path(user_id, file_id)
            media_type = "application/pdf"
        else:
            path = resource_service.get_content_path(user_id, file_id)
            media_type = "text/plain; charset=utf-8"
        return FileResponse(path, media_type=media_type)
    except ResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/avatars/{filename}")
def get_avatar(filename: str) -> FileResponse:
    from pathlib import Path
    from app.core.config import get_settings
    avatar_dir = Path(get_settings().avatar_dir)
    filepath = avatar_dir / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="头像不存在")
    ext = filepath.suffix.lower()
    media_type = "image/png"
    if ext in (".jpg", ".jpeg"):
        media_type = "image/jpeg"
    elif ext == ".webp":
        media_type = "image/webp"
    elif ext == ".gif":
        media_type = "image/gif"
    return FileResponse(filepath, media_type=media_type)


@router.get("/resources/{file_id}/content")
def get_resource_content(file_id: str, user_id: str) -> dict:
    try:
        content = resource_service.get_resource_content(user_id, file_id)
        return {"content": content}
    except ResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/resources/{file_id}", status_code=204)
def delete_resource(file_id: str, user_id: str) -> None:
    try:
        resource_service.delete(user_id, file_id)
    except ResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/resources/generated", status_code=201)
def save_generated_resource(request: SaveGeneratedResourceRequest) -> dict:
    try:
        resource = resource_service.save_generated_resource(
            user_id=request.user_id,
            name=request.name,
            content=request.content,
            resource_type=request.resource_type,
            course_folder=request.course_folder,
        )
        return {"resource": resource}
    except ResourceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/resources/{file_id}/folder")
def update_resource_folder(file_id: str, request: UpdateResourceFolderRequest) -> dict:
    try:
        resource = resource_service.update_resource_folder(
            request.user_id, file_id, request.course_folder
        )
        return {"resource": resource}
    except ResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/resources/categories/list")
def list_categories(user_id: str) -> dict:
    return {"categories": resource_service.list_categories(user_id)}


COURSE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "database_system",
        "name": "数据库系统",
        "icon": "DB",
        "description": "覆盖关系模型、SQL、函数依赖、范式、事务、并发控制、索引与存储管理。",
        "progress": 75,
        "totalHours": 32,
        "completedHours": 24,
        "status": "in-progress",
        "lastAccess": "2小时前",
        "difficulty": "中等",
        "chapters": [
            {"id": "db-01", "name": "数据库系统导论", "hours": 3, "status": "completed", "topics": ["数据模型", "数据库系统结构"]},
            {"id": "db-02", "name": "关系模型与关系代数", "hours": 5, "status": "completed", "topics": ["关系", "主码", "关系运算"]},
            {"id": "db-03", "name": "SQL 基础与查询", "hours": 6, "status": "current", "topics": ["SELECT", "JOIN", "GROUP BY"]},
            {"id": "db-04", "name": "函数依赖与范式", "hours": 6, "status": "pending", "topics": ["候选码", "2NF", "3NF", "BCNF"]},
            {"id": "db-05", "name": "事务与并发控制", "hours": 6, "status": "pending", "topics": ["ACID", "调度", "锁"]},
            {"id": "db-06", "name": "索引与存储管理", "hours": 6, "status": "pending", "topics": ["B+树", "索引选择", "磁盘组织"]},
        ],
        "goals": ["理解关系数据库的核心模型与约束", "能够编写常见 SQL 查询并解释执行意图", "掌握函数依赖、候选码和范式判断方法", "理解事务 ACID、并发异常和锁机制"],
        "suggestions": ["先复习 SQL JOIN 与 GROUP BY", "用小关系模式手算候选码闭包", "完成范式判断与事务调度练习"],
        "questions": [
            {
                "id": "db-q1",
                "type": "single",
                "chapter": "关系模型",
                "question": "关系模型中用于唯一标识元组的属性组称为什么？",
                "options": [{"label": "A", "text": "外码"}, {"label": "B", "text": "候选码"}, {"label": "C", "text": "视图"}, {"label": "D", "text": "索引"}],
                "answer": "B",
                "analysis": "候选码能够唯一标识关系中的每一个元组，且不含多余属性。",
            },
            {
                "id": "db-q2",
                "type": "judge",
                "chapter": "事务",
                "question": "事务的隔离性要求并发执行的结果与某种串行执行结果等价。",
                "options": [],
                "answer": True,
                "analysis": "隔离性强调并发事务之间互不干扰，常用可串行化来刻画正确性。",
            },
        ],
    },
    {
        "id": "data_structure",
        "name": "数据结构",
        "icon": "DS",
        "description": "覆盖线性表、栈、队列、树、图、查找与排序等基础结构和算法操作。",
        "progress": 60,
        "totalHours": 40,
        "completedHours": 24,
        "status": "in-progress",
        "lastAccess": "1天前",
        "difficulty": "困难",
        "chapters": [
            {"id": "ds-01", "name": "线性表", "hours": 5, "status": "completed", "topics": ["顺序表", "链表"]},
            {"id": "ds-02", "name": "栈与队列", "hours": 5, "status": "completed", "topics": ["LIFO", "FIFO", "循环队列"]},
            {"id": "ds-03", "name": "树与二叉树", "hours": 8, "status": "current", "topics": ["遍历", "完全二叉树", "哈夫曼树"]},
            {"id": "ds-04", "name": "图", "hours": 8, "status": "pending", "topics": ["DFS", "BFS", "最短路径"]},
            {"id": "ds-05", "name": "查找与排序", "hours": 10, "status": "pending", "topics": ["哈希", "二分查找", "快速排序"]},
        ],
        "goals": ["掌握常见数据结构的存储方式", "能够分析基本操作复杂度", "能根据问题选择合适结构"],
        "suggestions": ["重点练习树的遍历与性质", "把栈队列操作画成状态变化图", "排序题注意稳定性和复杂度"],
        "questions": [
            {
                "id": "ds-q1",
                "type": "single",
                "chapter": "栈与队列",
                "question": "栈的主要操作特点是？",
                "options": [{"label": "A", "text": "先进先出"}, {"label": "B", "text": "后进先出"}, {"label": "C", "text": "随机访问"}, {"label": "D", "text": "按关键字访问"}],
                "answer": "B",
                "analysis": "栈是后进先出结构，最后压入的元素最先弹出。",
            }
        ],
    },
    {
        "id": "algorithm_design",
        "name": "算法设计",
        "icon": "ALG",
        "description": "围绕复杂度分析、分治、贪心、动态规划、回溯与图算法建立解题方法。",
        "progress": 45,
        "totalHours": 48,
        "completedHours": 21,
        "status": "in-progress",
        "lastAccess": "3天前",
        "difficulty": "困难",
        "chapters": [
            {"id": "alg-01", "name": "复杂度分析", "hours": 6, "status": "completed", "topics": ["Big-O", "递推式"]},
            {"id": "alg-02", "name": "分治法", "hours": 8, "status": "completed", "topics": ["归并排序", "二分"]},
            {"id": "alg-03", "name": "动态规划", "hours": 10, "status": "current", "topics": ["最优子结构", "状态转移"]},
            {"id": "alg-04", "name": "贪心算法", "hours": 8, "status": "pending", "topics": ["选择性质", "证明"]},
            {"id": "alg-05", "name": "回溯与搜索", "hours": 8, "status": "pending", "topics": ["剪枝", "状态空间树"]},
        ],
        "goals": ["能够识别算法设计范式", "能够写出状态定义和转移方程", "能够分析时间与空间复杂度"],
        "suggestions": ["动态规划先写状态含义", "贪心题要补充正确性证明", "复杂度题注意最坏情况"],
        "questions": [
            {
                "id": "alg-q1",
                "type": "single",
                "chapter": "动态规划",
                "question": "动态规划通常适用于具备哪些性质的问题？",
                "options": [{"label": "A", "text": "最优子结构和重叠子问题"}, {"label": "B", "text": "完全随机"}, {"label": "C", "text": "只需一次比较"}, {"label": "D", "text": "无状态依赖"}],
                "answer": "A",
                "analysis": "动态规划通过保存重叠子问题结果，并利用最优子结构构造整体最优解。",
            }
        ],
    },
    {
        "id": "operating_system",
        "name": "操作系统",
        "icon": "OS",
        "description": "覆盖进程线程、调度、同步互斥、内存管理、文件系统与 I/O 管理。",
        "progress": 30,
        "totalHours": 36,
        "completedHours": 11,
        "status": "in-progress",
        "lastAccess": "1周前",
        "difficulty": "中等",
        "chapters": [
            {"id": "os-01", "name": "进程与线程", "hours": 7, "status": "completed", "topics": ["PCB", "上下文切换"]},
            {"id": "os-02", "name": "处理机调度", "hours": 6, "status": "current", "topics": ["FCFS", "SJF", "RR"]},
            {"id": "os-03", "name": "同步与死锁", "hours": 8, "status": "pending", "topics": ["信号量", "死锁条件"]},
            {"id": "os-04", "name": "内存管理", "hours": 8, "status": "pending", "topics": ["分页", "页面置换"]},
        ],
        "goals": ["理解进程调度与同步机制", "能够判断死锁必要条件", "掌握分页和页面置换基本方法"],
        "suggestions": ["调度题按时间轴推演", "死锁题先列资源分配关系", "页面置换题逐步记录页框"],
        "questions": [
            {
                "id": "os-q1",
                "type": "single",
                "chapter": "进程调度",
                "question": "LRU 通常属于哪类算法？",
                "options": [{"label": "A", "text": "进程调度"}, {"label": "B", "text": "页面置换"}, {"label": "C", "text": "磁盘调度"}, {"label": "D", "text": "文件分配"}],
                "answer": "B",
                "analysis": "LRU 是最近最久未使用页面置换算法，用于虚拟内存管理。",
            }
        ],
    },
    {
        "id": "computer_network",
        "name": "计算机网络",
        "icon": "NET",
        "description": "覆盖网络体系结构、TCP/IP、路由、可靠传输、拥塞控制与应用层协议。",
        "progress": 100,
        "totalHours": 30,
        "completedHours": 30,
        "status": "completed",
        "lastAccess": "2周前",
        "difficulty": "中等",
        "chapters": [
            {"id": "net-01", "name": "网络体系结构", "hours": 5, "status": "completed", "topics": ["OSI", "TCP/IP"]},
            {"id": "net-02", "name": "传输层", "hours": 8, "status": "completed", "topics": ["TCP", "UDP", "拥塞控制"]},
            {"id": "net-03", "name": "网络层", "hours": 8, "status": "completed", "topics": ["IP", "路由"]},
            {"id": "net-04", "name": "应用层", "hours": 5, "status": "completed", "topics": ["HTTP", "DNS"]},
        ],
        "goals": ["理解分层体系结构", "掌握 TCP 可靠传输机制", "能解释常见应用层协议工作流程"],
        "suggestions": ["复习 TCP 三次握手", "对照 OSI 和 TCP/IP 分层", "用报文流梳理 HTTP 与 DNS"],
        "questions": [
            {
                "id": "net-q1",
                "type": "single",
                "chapter": "应用层",
                "question": "HTTP 协议主要工作在哪一层？",
                "options": [{"label": "A", "text": "应用层"}, {"label": "B", "text": "网络层"}, {"label": "C", "text": "数据链路层"}, {"label": "D", "text": "物理层"}],
                "answer": "A",
                "analysis": "HTTP 是典型应用层协议，运行在 TCP 等传输服务之上。",
            }
        ],
    },
]


@router.get("/courses")
def course_catalog() -> dict:
    return {"courses": COURSE_CATALOG}


@router.get("/course-materials")
def list_course_materials(course: str) -> dict:
    return {"materials": course_material_service.list_materials(course)}


@router.get("/course-materials/{material_id}/preview")
def preview_course_material(material_id: str, course: str) -> FileResponse:
    try:
        return FileResponse(
            course_material_service.material_path(course, material_id),
            media_type="application/pdf",
        )
    except CourseMaterialError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/course-materials/{material_id}/annotations")
def list_course_material_annotations(material_id: str, user_id: str, course: str) -> dict:
    try:
        annotations = course_material_service.list_annotations(user_id, course, material_id)
        return {"annotations": annotations}
    except CourseMaterialError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/course-materials/{material_id}/annotations", status_code=201)
def add_course_material_annotation(material_id: str, request: CoursePdfAnnotationRequest) -> dict:
    try:
        annotation = course_material_service.add_annotation(
            user_id=request.user_id,
            course=request.course,
            material_id=material_id,
            page=request.page,
            content=request.content,
            x=request.x,
            y=request.y,
        )
        return {"annotation": annotation}
    except CourseMaterialError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/course-materials/{material_id}/annotations/{annotation_id}", status_code=204)
def delete_course_material_annotation(
    material_id: str,
    annotation_id: str,
    user_id: str,
    course: str,
) -> None:
    try:
        course_material_service.delete_annotation(user_id, course, material_id, annotation_id)
    except CourseMaterialError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/evaluate")
def evaluate(request: EvaluateRequest) -> dict:
    result = _evaluate_answers(request.model_dump())
    result["dynamic_profile"] = profile_service.update_from_evaluation(
        user_id=request.user_id, course=request.course, result=result
    )
    return result


@router.get("/workflow")
def workflow() -> dict:
    return _workflow_description()


@router.get("/profiles/{user_id}/subjects")
def list_dynamic_profiles(user_id: str) -> dict:
    return {"profiles": profile_service.list_profiles(user_id)}


@router.get("/learning/stats/{user_id}")
def get_learning_stats(user_id: str, course: str | None = None) -> dict:
    from app.learning.stats_service import LearningStatsService
    stats_service = LearningStatsService()
    if course:
        return {"stats": stats_service.get_course_stats(user_id, course)}
    return {"stats": stats_service.get_overall_stats(user_id)}


@router.get("/profiles/{user_id}")
def get_dynamic_profile(user_id: str, course: str | None = None) -> dict:
    return {"profile": profile_service.get_profile(user_id, course)}


@router.post("/profiles/chat")
def chat_dynamic_profile(request: ProfileChatRequest) -> dict:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="对话内容不能为空")
    return profile_service.update_from_chat(**request.model_dump())


@router.post("/profiles/interview/next")
def next_profile_interview_question(request: ProfileInterviewRequest) -> dict:
    return profile_service.next_question(**request.model_dump())


@router.post("/evaluate/smart")
def smart_evaluate(request: SmartEvaluateRequest) -> dict:
    profile = profile_service.get_profile(request.user_id, request.course)
    if not profile:
        raise HTTPException(status_code=404, detail="学生画像不存在，请先进行学习分析")
    
    recent_evaluations = profile.get("recent_evaluations", [])
    learning_progress = profile.get("learning_progress", {})
    
    dimensions = profile.get("dimensions", {})
    weak_points = dimensions.get("易错点", {}).get("value", [])
    if not weak_points:
        weak_points = ["函数依赖", "范式判断"]
    
    avg_score = 0
    if recent_evaluations:
        avg_score = round(sum(e.get("score", 0) for e in recent_evaluations) / len(recent_evaluations))
    
    completed_topics = [k for k, v in learning_progress.items() if v > 70]
    in_progress_topics = [k for k, v in learning_progress.items() if 30 <= v <= 70]
    weak_topics = [k for k, v in learning_progress.items() if v < 30]
    
    return {
        "user_id": request.user_id,
        "course": request.course,
        "profile_summary": {
            "knowledge_level": dimensions.get("知识基础", {}).get("value", "初级"),
            "learning_style": dimensions.get("认知风格", {}).get("value", "视觉型"),
            "learning_goal": dimensions.get("学习目标", {}).get("value", "考试准备"),
        },
        "score_summary": {
            "total": len(recent_evaluations) + 1,
            "correct": avg_score,
            "wrong": 100 - avg_score,
            "accuracy": avg_score,
        },
        "weak_points": weak_points + weak_topics,
        "completed_topics": completed_topics,
        "in_progress_topics": in_progress_topics,
        "analysis": f"""基于您的学习画像分析：
- 您的知识水平目前处于{profile.get('knowledge_level', '初级')}阶段
- 学习风格为{profile.get('learning_style', '视觉型')}，建议多使用图表和思维导图
- 已掌握的知识点：{', '.join(completed_topics) if completed_topics else '暂无'}
- 需要加强的知识点：{', '.join(weak_points + weak_topics)}

综合评估：您的整体表现{'优秀' if avg_score >= 80 else '良好' if avg_score >= 60 else '需加强'}，建议重点复习薄弱环节。""",
        "next_steps": [
            f"重点复习：{', '.join(weak_points[:2])}",
            "完成相关章节的练习题",
            "观看教学视频加深理解",
            "进行一次模拟测试检验学习效果",
        ],
        "dynamic_profile": profile,
    }


quiz_question_bank = [
    {
        "question_id": "q1",
        "question": "在关系数据库中，以下哪个范式要求消除非主属性对码的部分函数依赖？",
        "options": ["第一范式(1NF)", "第二范式(2NF)", "第三范式(3NF)", "BCNF"],
        "type": "single",
        "topic": "范式判断",
        "answer": "B",
        "explanation": "第二范式(2NF)要求在第一范式的基础上，消除非主属性对码的部分函数依赖。",
    },
    {
        "question_id": "q2",
        "question": "设有关系模式R(A,B,C,D)，函数依赖集F={A→B,B→C,A→D}，则R的候选码是？",
        "options": ["A", "AB", "AD", "ABC"],
        "type": "single",
        "topic": "候选码",
        "answer": "A",
        "explanation": "根据函数依赖A→B,B→C,A→D，A可以决定所有属性，因此A是候选码。",
    },
    {
        "question_id": "q3",
        "question": "函数依赖X→Y成立的条件是：对于关系模式R的任意两个元组，如果它们在X上的值相等，则它们在Y上的值也必须相等。",
        "options": ["正确", "错误"],
        "type": "judge",
        "topic": "函数依赖",
        "answer": "A",
        "explanation": "这是函数依赖的基本定义，体现了数据的完整性约束。",
    },
    {
        "question_id": "q4",
        "question": "在SQL中，用于查询多个表数据的关键字是？",
        "options": ["SELECT", "JOIN", "WHERE", "FROM"],
        "type": "single",
        "topic": "SQL基础",
        "answer": "B",
        "explanation": "JOIN关键字用于将两个或多个表按照关联条件组合在一起。",
    },
    {
        "question_id": "q5",
        "question": "事务的ACID特性包括：原子性(Atomicity)、一致性(Consistency)、隔离性(Isolation)和______。",
        "options": None,
        "type": "fill",
        "topic": "事务",
        "answer": "持久性",
        "explanation": "事务的第四个特性是持久性(Durability)，即事务提交后对数据库的修改是永久的。",
    },
]

current_quizzes: dict[str, dict] = {}


@router.post("/evaluate/quiz/start")
def start_quiz(request: SmartEvaluateRequest) -> dict:
    profile = profile_service.get_profile(request.user_id, request.course)
    weak_points = profile.get("dimensions", {}).get("易错点", {}).get("value", []) if profile else []
    if not weak_points:
        weak_points = ["函数依赖", "范式判断"]
    
    questions = []
    for q in quiz_question_bank:
        if q["topic"] in weak_points or len(questions) < 3:
            questions.append(QuizQuestion(**{k: v for k, v in q.items() if k != "answer" and k != "explanation"}))
    
    current_quizzes[request.user_id] = {
        "course": request.course,
        "questions": questions,
        "answers": {},
        "current_index": 0,
    }
    
    return {
        "user_id": request.user_id,
        "total_questions": len(questions),
        "current_index": 0,
        "question": questions[0] if questions else None,
    }


@router.post("/evaluate/quiz/answer")
def answer_quiz(request: QuizAnswerRequest) -> dict:
    quiz = current_quizzes.get(request.user_id)
    if not quiz:
        raise HTTPException(status_code=400, detail="请先开始测试")
    
    quiz["answers"][request.question_id] = request.answer
    
    current_idx = next((i for i, q in enumerate(quiz["questions"]) if q.question_id == request.question_id), -1)
    if current_idx == -1:
        raise HTTPException(status_code=400, detail="题目不存在")
    
    if current_idx < len(quiz["questions"]) - 1:
        next_question = quiz["questions"][current_idx + 1]
        return {
            "user_id": request.user_id,
            "total_questions": len(quiz["questions"]),
            "current_index": current_idx + 1,
            "question": next_question,
            "is_last": False,
        }
    else:
        return {
            "user_id": request.user_id,
            "total_questions": len(quiz["questions"]),
            "current_index": current_idx + 1,
            "question": None,
            "is_last": True,
        }


@router.post("/evaluate/quiz/finish")
def finish_quiz(request: SmartEvaluateRequest) -> dict:
    quiz = current_quizzes.get(request.user_id)
    if not quiz:
        raise HTTPException(status_code=400, detail="请先开始测试")
    
    correct_count = 0
    weak_points = []
    
    for q in quiz["questions"]:
        user_answer = quiz["answers"].get(q.question_id)
        correct_answer = next(item["answer"] for item in quiz_question_bank if item["question_id"] == q.question_id)
        
        if str(user_answer).strip().lower() == str(correct_answer).strip().lower():
            correct_count += 1
        else:
            weak_points.append(q.topic)
    
    accuracy = round((correct_count / len(quiz["questions"])) * 100)
    
    result = {
        "user_id": request.user_id,
        "course": quiz["course"],
        "score_summary": {
            "total": len(quiz["questions"]),
            "correct": correct_count,
            "wrong": len(quiz["questions"]) - correct_count,
            "accuracy": accuracy,
        },
        "weak_points": weak_points or ["函数依赖", "范式判断"],
        "analysis": f"测试完成！您答对了{correct_count}题，正确率{accuracy}%。{'表现优秀！继续保持。' if accuracy >= 80 else '表现良好，还有提升空间。' if accuracy >= 60 else '需要加强练习，建议复习相关知识点。'}",
        "next_steps": [
            f"复习薄弱知识点：{', '.join(weak_points[:2])}",
            "完成更多练习题",
            "观看相关教学视频",
            "定期进行模拟测试",
        ],
        "detailed_results": [
            {
                "question_id": q.question_id,
                "question": q.question,
                "user_answer": quiz["answers"].get(q.question_id),
                "correct_answer": next(item["answer"] for item in quiz_question_bank if item["question_id"] == q.question_id),
                "is_correct": str(quiz["answers"].get(q.question_id)).strip().lower() == str(next(item["answer"] for item in quiz_question_bank if item["question_id"] == q.question_id)).strip().lower(),
                "explanation": next(item["explanation"] for item in quiz_question_bank if item["question_id"] == q.question_id),
            }
            for q in quiz["questions"]
        ],
    }
    
    result["dynamic_profile"] = profile_service.update_from_evaluation(
        user_id=request.user_id, course=quiz["course"], result=result
    )
    del current_quizzes[request.user_id]
    
    return result


@router.post("/settings/siliconflow/test")
def test_siliconflow(request: SiliconFlowConfig) -> dict:
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="请输入硅基流动 API Key")
    try:
        return profile_service.test_connection(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/settings/spark/test")
def test_spark(request: SiliconFlowConfig) -> dict:
    try:
        return profile_service.test_spark_connection(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ========== 错题本 API ==========

from app.mistakes.store import MistakeStore

mistake_store = MistakeStore()


@router.post("/mistakes/add")
def add_mistake(request: QuizAnswerRequest) -> dict:
    mistake_store.add_mistake(
        user_id=request.user_id,
        course=request.course,
        record={
            "question_id": request.question_id,
            "question": request.question,
            "type": request.type,
            "chapter": request.chapter,
            "level": request.level,
            "options": request.options,
            "student_answer": request.answer,
            "correct_answer": request.correct_answer,
            "analysis": request.analysis,
            "topic": request.topic,
        }
    )
    return {"status": "ok"}


@router.get("/mistakes/list")
def list_mistakes(user_id: str, course: str) -> dict:
    mistakes = mistake_store.list_mistakes(user_id, course)
    return {"mistakes": mistakes}


@router.post("/mistakes/master")
def mark_mistake_mastered(user_id: str = Form(...), course: str = Form(...), question_id: str = Form(...)) -> dict:
    mistake_store.mark_mastered(user_id, course, question_id)
    return {"status": "ok"}


@router.get("/mistakes/weak-topics")
def get_weak_topics(user_id: str, course: str) -> dict:
    topics = mistake_store.get_weak_topics(user_id, course)
    return {"topics": topics}

@router.get("/mistakes/all")
def list_all_mistakes(user_id: str, mastered: bool = False) -> dict:
    mistakes = mistake_store.list_all_mistakes(user_id, mastered)
    return {"mistakes": mistakes}

@router.get("/mistakes/stats")
def get_mistake_stats(user_id: str) -> dict:
    stats = mistake_store.get_mistake_stats(user_id)
    return {"stats": stats}

@router.post("/mistakes/master-any")
def mark_mastered_any_course(user_id: str, question_id: str) -> dict:
    mistake_store.mark_mastered_any_course(user_id, question_id)
    return {"status": "ok"}
