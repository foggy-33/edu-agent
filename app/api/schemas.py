from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class LearningRequest(BaseModel):
    user_id: str = Field(..., examples=["demo_user_001"])
    course: str = Field(..., examples=["数据库系统"])
    message: str = Field(..., examples=["我对函数依赖、候选码和范式判断不太会，希望通过例题准备考试。"])


class RegisterRequest(BaseModel):
    username: str
    display_name: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SiliconFlowConfig(BaseModel):
    api_key: str = ""
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "Pro/deepseek-ai/DeepSeek-V3.2"


class CollaborativeLearningRequest(SiliconFlowConfig):
    major: str
    course: str
    chapter: str
    weakness: str
    goal: str
    resourceTypes: list[Literal["lecture", "mindmap", "exercise", "reading", "code", "video"]]


class ProfileChatRequest(SiliconFlowConfig):
    user_id: str = "demo_user_001"
    course: str = "数据库系统"
    message: str


class ProfileInterviewRequest(SiliconFlowConfig):
    user_id: str = "demo_user_001"
    course: str = "数据库系统"


class AnswerRecord(BaseModel):
    question_id: str | None = None
    question: str
    student_answer: str
    correct_answer: str | None = None
    is_correct: bool | None = None
    topic: str | None = None


class EvaluateRequest(BaseModel):
    user_id: str
    course: str = "数据库系统"
    answers: list[AnswerRecord] = Field(default_factory=list)
    message: str | None = None


class SmartEvaluateRequest(BaseModel):
    user_id: str
    course: str = "数据库系统"


class QuizQuestion(BaseModel):
    question_id: str
    question: str
    options: list[str] | None = None
    type: Literal["single", "multiple", "judge", "fill", "essay"]
    topic: str


class QuizAnswerRequest(BaseModel):
    user_id: str
    course: str = "数据库系统"
    question_id: str
    answer: str | list[str]


class StudentProfile(BaseModel):
    major: str
    course: str
    grade_level: str
    learning_goal: str
    knowledge_level: str
    weak_points: list[str]
    learning_style: str
    resource_preference: list[str]


class LearningPathItem(BaseModel):
    stage: int
    title: str
    goal: str
    tasks: list[str]
    estimated_time: str
    recommended_resources: list[str]


class QuizItem(BaseModel):
    question: str
    type: Literal["选择题", "判断题", "填空题", "简答题", "应用题"]
    answer: str
    explanation: str


class Resources(BaseModel):
    document: str
    mindmap: str
    quiz: list[QuizItem]
    practice_case: str
    extended_reading: list[dict[str, str]]


class SafetyReport(BaseModel):
    status: Literal["pass", "warning"]
    notes: list[str]


class GenerateResponse(BaseModel):
    profile: StudentProfile
    learning_path: list[LearningPathItem]
    resources: Resources
    safety_report: SafetyReport


class EvaluateResponse(BaseModel):
    user_id: str
    course: str
    score_summary: dict[str, Any]
    weak_points: list[str]
    analysis: str
    next_steps: list[str]
