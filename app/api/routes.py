import json
from typing import Any, Iterator

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.profile_agent import ProfileAgent
from app.api.schemas import (
    CollaborativeLearningRequest,
    EvaluateRequest,
    LearningRequest,
    LoginRequest,
    ProfileChatRequest,
    ProfileInterviewRequest,
    QuizAnswerRequest,
    QuizQuestion,
    RegisterRequest,
    SiliconFlowConfig,
    SmartEvaluateRequest,
)
from app.auth.service import AuthError, AuthService
from app.graph.workflow import run_agent_workflow, workflow_description
from app.learning.agents import (
    _context,
    _exercises_to_markdown,
    _generate_exercise_items,
    _mindmap_label,
    _source_note,
    _source_points,
    _trace,
    integration_agent,
    planner_agent,
    profile_agent,
    review_agent,
)
from app.learning.llm import stream_llm
from app.learning.state import LearningState
from app.learning.workflow import generate_learning_resources
from app.profiles.service import DynamicProfileService
from app.resources.service import ResourceError, ResourceService

router = APIRouter()
profile_service = DynamicProfileService()
auth_service = AuthService()
resource_service = ResourceService()


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    return authorization.removeprefix("Bearer ").strip()


def _collaborative_payload(request: CollaborativeLearningRequest) -> dict[str, Any]:
    payload = request.model_dump()
    source_context, sources = resource_service.build_context(request.user_id, request.fileIds)
    payload["source_context"] = source_context
    payload["sources"] = sources
    return payload


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
    ):
        collected.append(chunk)
        yield _sse("content", {"key": key, "text": chunk})

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


@router.post("/analyze")
def analyze(request: LearningRequest) -> dict:
    profile = ProfileAgent().run(
        {
            "user_id": request.user_id,
            "course": request.course,
            "message": request.message,
        }
    )
    return {"profile": profile}


@router.post("/generate")
def generate(request: LearningRequest) -> dict:
    return run_agent_workflow(
        {
            "user_id": request.user_id,
            "course": request.course,
            "message": request.message,
        }
    )


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
            yield _sse("status", {"message": "正在读取问题和已选资料"})
            payload = _collaborative_payload(request)
            state = LearningState(**payload, agentTrace=[])
            if payload.get("source_context"):
                yield _sse("status", {"message": "已整理引用资料，准备生成回答"})
            else:
                yield _sse("status", {"message": "未引用资料，直接围绕问题生成回答"})

            if not request.resourceTypes:
                yield _sse("status", {"message": "直接对话模式，正在组织回答", "agent": "直接对话 Agent"})
                state["lectureDoc"] = yield from _stream_generated_text(
                    state,
                    "lectureDoc",
                    "直接回答用户的问题。保持中文、清晰、可执行；如果用户引用了 PDF，优先依据资料回答，资料不足时说明是补充解释。",
                    _direct_chat_fallback(state),
                )
                state["agentTrace"] = _trace(state, "直接对话 Agent", "已生成直接对话回答")
                yield _sse("status", {"message": "已生成直接对话回答", "agent": "直接对话 Agent"})
                yield _sse("done", {"result": _learning_result(state)})
                return

            yield _sse("status", {"message": f"已选择 {len(request.resourceTypes)} 类资源，正在调度协作 Agent"})

            for node in (profile_agent, planner_agent):
                state.update(node(state))
                trace = state.get("agentTrace", [])[-1]
                yield _sse("status", {"message": trace.get("summary", ""), "agent": trace.get("agent", "")})

            if "lecture" in request.resourceTypes:
                yield _sse("status", {"message": "正在流式生成课程讲解", "agent": "课程讲解 Agent"})
                state["lectureDoc"] = yield from _stream_generated_text(
                    state,
                    "lectureDoc",
                    "生成 Markdown 课程讲解文档，必须包含概念解释、原理说明、例子、易错点和复习建议。",
                    _lecture_fallback(state),
                )
                state["agentTrace"] = _trace(state, "课程讲解 Agent", "课程讲解文档生成完成")
                yield _sse("status", {"message": "课程讲解文档生成完成", "agent": "课程讲解 Agent"})

            if "mindmap" in request.resourceTypes:
                yield _sse("status", {"message": "正在流式生成思维导图", "agent": "思维导图 Agent"})
                state["mindmap"] = yield from _stream_generated_text(
                    state,
                    "mindmap",
                    "只输出 Mermaid mindmap 源码，提炼所选 PDF 或用户问题中的主题、核心概念、层级关系、应用与易错点。",
                    _mindmap_fallback(state),
                )
                state["agentTrace"] = _trace(state, "思维导图 Agent", "Mermaid 思维导图生成完成")
                yield _sse("status", {"message": "Mermaid 思维导图生成完成", "agent": "思维导图 Agent"})

            if "exercise" in request.resourceTypes:
                yield _sse("status", {"message": "正在生成可作答练习题", "agent": "练习题 Agent"})
                items = _generate_exercise_items(state)
                state["exerciseItems"] = items
                state["exercises"] = _exercises_to_markdown(state, items)
                state["agentTrace"] = _trace(state, "练习题 Agent", "可在线作答的分层练习题生成完成")
                yield from _stream_text("exercises", state["exercises"])
                yield _sse("status", {"message": "可在线作答的分层练习题生成完成", "agent": "练习题 Agent"})

            if "reading" in request.resourceTypes:
                yield _sse("status", {"message": "正在流式生成拓展阅读", "agent": "拓展阅读 Agent"})
                state["reading"] = yield from _stream_generated_text(
                    state,
                    "reading",
                    "生成 Markdown 拓展阅读，包含相关知识延伸、实际应用场景和递进学习路径。",
                    _reading_fallback(state),
                )
                state["agentTrace"] = _trace(state, "拓展阅读 Agent", "知识延伸与学习路径生成完成")
                yield _sse("status", {"message": "知识延伸与学习路径生成完成", "agent": "拓展阅读 Agent"})

            state.update(review_agent(state))
            yield from _stream_text("review", state.get("review", ""))
            trace = state.get("agentTrace", [])[-1]
            yield _sse("status", {"message": trace.get("summary", ""), "agent": trace.get("agent", "")})

            state.update(integration_agent(state))
            trace = state.get("agentTrace", [])[-1]
            yield _sse("status", {"message": trace.get("summary", ""), "agent": trace.get("agent", "")})
            yield _sse("done", {"result": _learning_result(state)})
        except ResourceError as exc:
            yield _sse("error", {"message": str(exc)})
        except ValueError as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/resources/upload", status_code=201)
def upload_resource(user_id: str = Form(...), file: UploadFile = File(...)) -> dict:
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="仅支持上传 PDF 文件")
    try:
        return {"resource": resource_service.upload_pdf(user_id=user_id, filename=file.filename or "document.pdf", stream=file.file)}
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
        return FileResponse(
            resource_service.get_pdf_path(user_id, file_id),
            media_type="application/pdf",
            filename=metadata["name"],
        )
    except ResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/resources/{file_id}", status_code=204)
def delete_resource(file_id: str, user_id: str) -> None:
    try:
        resource_service.delete(user_id, file_id)
    except ResourceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/evaluate")
def evaluate(request: EvaluateRequest) -> dict:
    result = EvaluatorAgent().run(request.model_dump())
    result["dynamic_profile"] = profile_service.update_from_evaluation(
        user_id=request.user_id, course=request.course, result=result
    )
    return result


@router.get("/courses")
def courses() -> dict:
    return {
        "courses": [
            {
                "id": "database_system",
                "name": "数据库系统",
                "description": "关系模型、SQL、函数依赖、范式、事务、并发控制、索引与存储管理。",
            }
        ]
    }


@router.get("/workflow")
def workflow() -> dict:
    return workflow_description()


@router.get("/profiles/{user_id}/subjects")
def list_dynamic_profiles(user_id: str) -> dict:
    return {"profiles": profile_service.list_profiles(user_id)}


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
