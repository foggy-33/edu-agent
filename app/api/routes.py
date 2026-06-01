from fastapi import APIRouter

from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.profile_agent import ProfileAgent
from app.api.schemas import EvaluateRequest, LearningRequest
from app.graph.workflow import run_agent_workflow, workflow_description

router = APIRouter()


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
    return EvaluatorAgent().run(request.model_dump())


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
