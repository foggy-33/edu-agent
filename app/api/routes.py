from fastapi import APIRouter, Header, HTTPException

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
from app.learning.workflow import generate_learning_resources
from app.profiles.service import DynamicProfileService

router = APIRouter()
profile_service = DynamicProfileService()
auth_service = AuthService()


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    return authorization.removeprefix("Bearer ").strip()


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
    if not request.resourceTypes:
        raise HTTPException(status_code=400, detail="请至少选择一种资源类型")
    try:
        return generate_learning_resources(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/evaluate")
def evaluate(request: EvaluateRequest) -> dict:
    result = EvaluatorAgent().run(request.model_dump())
    result["dynamic_profile"] = profile_service.update_from_evaluation(user_id=request.user_id, result=result)
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


@router.get("/profiles/{user_id}")
def get_dynamic_profile(user_id: str) -> dict:
    return {"profile": profile_service.get_profile(user_id)}


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
    profile = profile_service.get_profile(request.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="学生画像不存在，请先进行学习分析")
    
    recent_evaluations = profile.get("recent_evaluations", [])
    learning_progress = profile.get("learning_progress", {})
    
    weak_points = profile.get("weak_points", [])
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
            "knowledge_level": profile.get("knowledge_level", "初级"),
            "learning_style": profile.get("learning_style", "视觉型"),
            "learning_goal": profile.get("learning_goal", "考试准备"),
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
    profile = profile_service.get_profile(request.user_id)
    weak_points = profile.get("weak_points", ["函数依赖", "范式判断"]) if profile else []
    
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
    
    result["dynamic_profile"] = profile_service.update_from_evaluation(user_id=request.user_id, result=result)
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
