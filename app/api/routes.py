from fastapi import APIRouter, HTTPException

from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.profile_agent import ProfileAgent
from app.api.schemas import EvaluateRequest, LearningRequest, ProfileChatRequest, ProfileInterviewRequest, SiliconFlowConfig
from app.graph.workflow import run_agent_workflow, workflow_description
from app.profiles.service import DynamicProfileService

router = APIRouter()
profile_service = DynamicProfileService()


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


@router.post("/settings/siliconflow/test")
def test_siliconflow(request: SiliconFlowConfig) -> dict:
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="请输入硅基流动 API Key")
    try:
        return profile_service.test_connection(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
