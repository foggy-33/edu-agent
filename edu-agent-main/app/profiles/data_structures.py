"""学生画像、学习记录、答题记录数据结构定义"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KnowledgeLevel(str, Enum):
    """知识水平枚举"""
    BEGINNER = "beginner"       # 初级
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"       # 高级


class LearningStyle(str, Enum):
    """学习风格枚举"""
    VISUAL = "visual"           # 视觉型：偏好图表、思维导图
    AUDITORY = "auditory"       # 听觉型：偏好视频、讲解
    READING = "reading"         # 阅读型：偏好文字讲义
    KINESTHETIC = "kinesthetic" # 动觉型：偏好动手实践


class QuestionType(str, Enum):
    """题目类型枚举"""
    SINGLE_CHOICE = "single"    # 单选题
    MULTIPLE_CHOICE = "multiple"  # 多选题
    TRUE_FALSE = "judge"        # 判断题
    FILL_BLANK = "fill"         # 填空题
    SHORT_ANSWER = "short"      # 简答题
    PROGRAMMING = "programming"  # 编程题


class AnswerResult(str, Enum):
    """答题结果枚举"""
    CORRECT = "correct"          # 正确
    INCORRECT = "incorrect"     # 错误
    PARTIAL = "partial"         # 部分正确
    SKIPPED = "skipped"         # 跳过


class ResourceType(str, Enum):
    """资源类型枚举"""
    DOCUMENT = "document"       # 文档
    MINDMAP = "mindmap"          # 思维导图
    QUIZ = "quiz"               # 测验
    PRACTICE = "practice"        # 练习
    VIDEO = "video"              # 视频
    OTHER = "other"              # 其他


# ============================================================
# 学生画像数据结构
# ============================================================

class DimensionValue(BaseModel):
    """画像维度值"""
    value: Any                    # 维度值（字符串或列表）
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)  # 置信度
    updated_at: str              # 更新时间 ISO格式
    evidence: str = ""           # 证据/来源


class StudentProfile(BaseModel):
    """学生画像完整数据结构"""
    # 基本信息
    user_id: str = Field(description="学生唯一标识")
    version: int = Field(default=0, description="画像版本号")
    course: str = Field(default="database_system", description="所属课程")
    
    # 画像维度
    dimensions: Dict[str, DimensionValue] = Field(
        default_factory=dict,
        description="画像维度字典"
    )
    
    # 维度目录
    dimension_catalog: List[str] = Field(
        default=[
            "专业与年级",
            "学习目标",
            "知识基础",
            "认知风格",
            "易错点",
            "资源偏好",
            "学习节奏",
            "学习动机",
        ],
        description="支持的画像维度列表"
    )
    
    # 统计信息
    completion: float = Field(default=0.0, ge=0.0, le=100.0, description="画像完成度百分比")
    total_learning_time: int = Field(default=0, description="累计学习时长(分钟)")
    total_questions: int = Field(default=0, description="累计答题数")
    correct_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="累计正确率")
    
    # 薄弱点与强项
    weak_points: List[str] = Field(default_factory=list, description="薄弱知识点列表")
    strong_points: List[str] = Field(default_factory=list, description="强项知识点列表")
    
    # 元数据
    created_at: str = Field(description="创建时间 ISO格式")
    updated_at: str = Field(description="更新时间 ISO格式")
    last_active_at: str = Field(description="最后活跃时间 ISO格式")
    
    # 历史记录
    history: List[Dict[str, Any]] = Field(default_factory=list, description="画像更新历史")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "student_001",
                "version": 5,
                "course": "database_system",
                "dimensions": {
                    "专业与年级": {
                        "value": "计算机科学 / 大二",
                        "confidence": 0.85,
                        "updated_at": "2025-01-15T10:30:00Z",
                        "evidence": "学生自我介绍"
                    },
                    "知识基础": {
                        "value": "中级",
                        "confidence": 0.75,
                        "updated_at": "2025-01-15T10:30:00Z",
                        "evidence": "已完成SQL基础章节"
                    }
                },
                "completion": 62.5,
                "total_learning_time": 180,
                "total_questions": 50,
                "correct_rate": 72.5,
                "weak_points": ["函数依赖", "范式判断"],
                "strong_points": ["SQL基础", "索引"],
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
                "last_active_at": "2025-01-15T10:30:00Z",
                "history": []
            }
        }


# ============================================================
# 学习记录数据结构
# ============================================================

class LearningActivity(BaseModel):
    """学习活动记录"""
    activity_id: str = Field(default="", description="活动唯一标识(UUID)")
    user_id: str = Field(description="学生ID")
    course: str = Field(default="database_system", description="课程")
    
    # 活动类型
    activity_type: str = Field(
        description="活动类型",
        examples=["read_document", "view_mindmap", "take_quiz", "practice_sql", "chat"]
    )
    
    # 资源信息
    resource_type: ResourceType = Field(default=ResourceType.OTHER, description="资源类型")
    resource_id: str = Field(default="", description="资源ID")
    resource_title: str = Field(default="", description="资源标题")
    resource_source: str = Field(default="", description="资源来源路径")
    
    # 学习内容摘要
    topic: str = Field(default="", description="涉及的知识点")
    content_summary: str = Field(default="", description="内容摘要")
    
    # 时间信息
    started_at: str = Field(default="", description="开始时间 ISO格式")
    ended_at: str = Field(default="", description="结束时间 ISO格式")
    duration_seconds: int = Field(default=0, description="学习时长(秒)")
    
    # 交互信息
    interaction_count: int = Field(default=0, description="交互次数")
    scroll_depth: float = Field(default=0.0, ge=0.0, le=1.0, description="浏览深度")
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="完成度")
    
    # 效果评估
    understanding_level: float = Field(default=0.0, ge=0.0, le=1.0, description="理解程度自评")
    difficulty_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="难度评分")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "activity_id": "act_20250115_001",
                "user_id": "student_001",
                "course": "database_system",
                "activity_type": "read_document",
                "resource_type": "document",
                "resource_id": "doc_06_normal_form",
                "resource_title": "数据库范式详解",
                "topic": "第三范式",
                "started_at": "2025-01-15T10:00:00Z",
                "ended_at": "2025-01-15T10:25:00Z",
                "duration_seconds": 1500,
                "interaction_count": 5,
                "scroll_depth": 0.85,
                "completion_rate": 1.0,
                "understanding_level": 0.75,
                "difficulty_rating": 3.0
            }
        }


class LearningSession(BaseModel):
    """学习会话（一段时间内的连续学习活动）"""
    session_id: str = Field(description="会话ID")
    user_id: str = Field(description="学生ID")
    course: str = Field(default="database_system", description="课程")
    
    # 时间范围
    started_at: str = Field(description="会话开始时间")
    ended_at: str = Field(default="", description="会话结束时间")
    
    # 会话统计
    total_duration_seconds: int = Field(default=0, description="总会话时长")
    activity_count: int = Field(default=0, description="活动数量")
    
    # 活动列表
    activities: List[LearningActivity] = Field(default_factory=list, description="活动列表")
    
    # 会话效果
    topics_covered: List[str] = Field(default_factory=list, description="涉及的知识点")
    topics_mastered: List[str] = Field(default_factory=list, description="掌握的知识点")
    
    # 效率指标
    focus_score: float = Field(default=0.0, ge=0.0, le=1.0, description="专注度得分")
    learning_efficiency: float = Field(default=0.0, ge=0.0, le=1.0, description="学习效率")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class LearningStatistics(BaseModel):
    """学习统计数据（日/周/月统计）"""
    user_id: str = Field(description="学生ID")
    course: str = Field(default="database_system", description="课程")
    period_type: str = Field(description="统计周期: daily/weekly/monthly")
    period_start: str = Field(description="周期开始日期")
    period_end: str = Field(description="周期结束日期")
    
    # 时间统计
    total_learning_time: int = Field(default=0, description="总学习时长(分钟)")
    active_days: int = Field(default=0, description="学习天数")
    average_session_length: int = Field(default=0, description="平均会话时长(分钟)")
    
    # 活动统计
    total_activities: int = Field(default=0, description="总活动数")
    activities_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")
    
    # 内容统计
    topics_covered: List[str] = Field(default_factory=list, description="学习的知识点")
    resources_accessed: int = Field(default=0, description="访问的资源数")
    
    # 答题统计（汇总）
    questions_attempted: int = Field(default=0, description="答题数")
    questions_correct: int = Field(default=0, description="正确数")
    correct_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="正确率")
    
    # 趋势指标
    improvement_rate: float = Field(default=0.0, description="进步率，相比上一周期")
    engagement_score: float = Field(default=0.0, ge=0.0, le=1.0, description="参与度得分")


# ============================================================
# 答题记录数据结构
# ============================================================

class AnswerRecord(BaseModel):
    """单条答题记录"""
    record_id: str = Field(default="", description="记录ID(UUID)")
    user_id: str = Field(description="学生ID")
    course: str = Field(default="database_system", description="课程")
    
    # 题目信息
    question_id: str = Field(default="", description="题目ID")
    question_text: str = Field(default="", description="题目内容")
    question_type: QuestionType = Field(default=QuestionType.SINGLE_CHOICE, description="题目类型")
    topic: str = Field(default="", description="知识点/主题")
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0, description="难度系数")
    
    # 答案信息
    user_answer: str = Field(default="", description="学生答案")
    correct_answer: str = Field(default="", description="正确答案")
    is_correct: AnswerResult = Field(default=AnswerResult.SKIPPED, description="答题结果")
    
    # 时间信息
    answered_at: str = Field(default="", description="答题时间")
    time_spent_seconds: int = Field(default=0, description="用时(秒)")
    
    # 分析信息
    score: float = Field(default=0.0, ge=0.0, le=100.0, description="得分")
    explanation: str = Field(default="", description="答案解析")
    
    # 关联信息
    source_quiz_id: str = Field(default="", description="来源测验ID")
    source_practice_id: str = Field(default="", description="来源练习ID")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "record_id": "ans_20250115_001",
                "user_id": "student_001",
                "course": "database_system",
                "question_id": "q_2nf_judge_01",
                "question_text": "在第二范式中，非主属性必须完全函数依赖于主键。",
                "question_type": "judge",
                "topic": "第二范式",
                "difficulty": 0.6,
                "user_answer": "正确",
                "correct_answer": "正确",
                "is_correct": "correct",
                "answered_at": "2025-01-15T14:30:00Z",
                "time_spent_seconds": 45,
                "score": 100.0,
                "explanation": "第二范式确实要求非主属性完全函数依赖于主键。"
            }
        }


class QuizAttempt(BaseModel):
    """一次测验尝试"""
    attempt_id: str = Field(default="", description="测验ID")
    user_id: str = Field(description="学生ID")
    course: str = Field(default="database_system", description="课程")
    
    # 测验信息
    quiz_title: str = Field(default="", description="测验标题")
    quiz_type: str = Field(default="practice", description="测验类型: practice/exam/quiz")
    topics: List[str] = Field(default_factory=list, description="涉及的知识点")
    
    # 时间
    started_at: str = Field(default="", description="开始时间")
    submitted_at: str = Field(default="", description="提交时间")
    total_time_seconds: int = Field(default=0, description="总用时")
    
    # 答题记录
    answers: List[AnswerRecord] = Field(default_factory=list, description="答题记录列表")
    
    # 统计结果
    total_questions: int = Field(default=0, description="总题数")
    correct_count: int = Field(default=0, description="正确数")
    incorrect_count: int = Field(default=0, description="错误数")
    skipped_count: int = Field(default=0, description="跳过数")
    score: float = Field(default=0.0, ge=0.0, le=100.0, description="总分")
    correct_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="正确率")
    
    # 详细分析
    weak_points: List[str] = Field(default_factory=list, description="暴露的薄弱点")
    strong_points: List[str] = Field(default_factory=list, description="表现好的知识点")
    time_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="各题目用时分布"
    )
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class TopicMastery(BaseModel):
    """知识点掌握度"""
    user_id: str = Field(description="学生ID")
    course: str = Field(default="database_system", description="课程")
    topic: str = Field(description="知识点名称")
    
    # 掌握度指标
    mastery_level: float = Field(default=0.0, ge=0.0, le=1.0, description="掌握度(0-1)")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="置信度")
    
    # 历史统计
    total_attempts: int = Field(default=0, description="总尝试次数")
    correct_attempts: int = Field(default=0, description="正确次数")
    historical_correct_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="历史正确率")
    
    # 趋势分析
    trend: str = Field(default="stable", description="趋势: improving/declining/stable")
    last_attempt_at: str = Field(default="", description="最近一次答题时间")
    attempts_history: List[Dict[str, Any]] = Field(default_factory=list, description="最近10次答题记录")
    
    # 建议
    recommended_action: str = Field(default="", description="推荐行动")
    priority: int = Field(default=0, description="优先级(数字越大优先级越高)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "student_001",
                "course": "database_system",
                "topic": "函数依赖",
                "mastery_level": 0.65,
                "confidence": 0.8,
                "total_attempts": 10,
                "correct_attempts": 7,
                "historical_correct_rate": 70.0,
                "trend": "improving",
                "last_attempt_at": "2025-01-15T14:30:00Z",
                "attempts_history": [
                    {"attempt_at": "2025-01-10", "is_correct": True},
                    {"attempt_at": "2025-01-12", "is_correct": False},
                    {"attempt_at": "2025-01-15", "is_correct": True}
                ],
                "recommended_action": "加强练习",
                "priority": 3
            }
        }


# ============================================================
# 存储配置
# ============================================================

class StorageConfig:
    """存储目录配置"""
    # 基础数据目录
    DATA_DIR = "data"
    
    # 子目录
    PROFILES_DIR = "profiles"
    LEARNING_DIR = "learning"
    ANSWERS_DIR = "answers"
    TOPICS_DIR = "topics"
    
    # 文件扩展名
    PROFILE_EXT = ".profile.json"
    LEARNING_SESSION_EXT = ".session.json"
    ANSWER_EXT = ".answer.json"
    QUIZ_EXT = ".quiz.json"
    TOPIC_MASTERY_EXT = ".topic.json"
    
    @classmethod
    def get_profile_path(cls, user_id: str) -> str:
        return f"{cls.DATA_DIR}/{cls.PROFILES_DIR}/{user_id}{cls.PROFILE_EXT}"
    
    @classmethod
    def get_learning_path(cls, user_id: str) -> str:
        return f"{cls.DATA_DIR}/{cls.LEARNING_DIR}/{user_id}"
    
    @classmethod
    def get_answer_path(cls, user_id: str) -> str:
        return f"{cls.DATA_DIR}/{cls.ANSWERS_DIR}/{user_id}"
    
    @classmethod
    def get_topic_path(cls, user_id: str) -> str:
        return f"{cls.DATA_DIR}/{cls.TOPICS_DIR}/{user_id}"
