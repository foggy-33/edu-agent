from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

app = FastAPI(
    title="edu-agent-ai",
    description="基于大模型的个性化资源生成与学习多智能体系统 AI 后端",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "service": "edu-agent-ai",
        "status": "running",
        "message": "FastAPI + LangGraph multi-agent service is ready.",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "edu-agent-ai"}


app.include_router(api_router, prefix="/api", tags=["AI Agents"])
