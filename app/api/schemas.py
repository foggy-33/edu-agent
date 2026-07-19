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
    active_provider: Literal["siliconflow", "spark", "openai"] = "siliconflow"
    api_key: str = ""
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "Pro/deepseek-ai/DeepSeek-V3.2"
    spark_api_password: str = ""
    spark_base_url: str = ""
    spark_model: str = ""
    openai_model: str = "gpt-5.6-sol"


class CollaborativeLearningRequest(SiliconFlowConfig):
    user_id: str = "demo_user_001"
    major: str
    course: str
    chapter: str
    weakness: str
    goal: str
    resourceTypes: list[Literal["lecture", "mindmap", "exercise", "reading", "code", "path"]]
    fileIds: list[str] = Field(default_factory=list)
    response_speed: Literal["fast", "balanced", "deep"] = "balanced"


class CoursePdfAnnotationRequest(BaseModel):
    user_id: str
    course: str
    page: int = Field(..., ge=1)
    content: str = Field(..., min_length=1, max_length=2000)
    x: float | None = Field(default=None, ge=0, le=1)
    y: float | None = Field(default=None, ge=0, le=1)


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


class MistakeWeaknessRequest(SiliconFlowConfig):
    user_id: str = "demo_user_001"
    course: str = ""


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
    question: str = ""
    answer: str | list[str]
    type: str = ""
    chapter: str = ""
    level: str = ""
    options: list[dict] | None = None
    correct_answer: str | None = None
    analysis: str = ""
    topic: str = ""


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


class OnboardingProfileRequest(BaseModel):
    grade_level: str = ""
    major: str = ""
    weak_subjects: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    learning_style: list[str] = Field(default_factory=list)
    learning_goal: str = ""
    school: str = ""


class OnboardingProfileResponse(BaseModel):
    onboarding_completed: bool
    onboarding_profile: dict[str, Any]


class SaveGeneratedResourceRequest(BaseModel):
    user_id: str
    name: str
    content: str
    resource_type: str = "markdown"
    course_folder: str = "AI生成"


class UpdateResourceFolderRequest(BaseModel):
    user_id: str
    course_folder: str


class UpdateUserProfileRequest(BaseModel):
    display_name: str = ""
    avatar: str = ""
    phone: str = ""
    email: str = ""
    school: str = ""
    major: str = ""
    grade_level: str = ""
    learning_goal: str = ""
