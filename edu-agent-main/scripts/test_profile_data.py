#!/usr/bin/env python3
"""
学生画像、学习记录、答题记录数据结构测试脚本
验证所有数据结构的创建、存储、读取功能
"""
import sys
import os
from datetime import datetime, timezone

# 设置项目路径
PROJECT_ROOT = r"C:\Users\wyh\Downloads\edu-agent-main (1)\edu-agent-main"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from app.profiles.data_structures import (
    AnswerRecord,
    AnswerResult,
    KnowledgeLevel,
    LearningActivity,
    LearningSession,
    LearningStatistics,
    LearningStyle,
    QuestionType,
    QuizAttempt,
    ResourceType,
    StorageConfig,
    StudentProfile,
    TopicMastery,
    DimensionValue,
)
from app.profiles.learning_record import LearningRecordStore
from app.profiles.answer_record import AnswerRecordStore


def print_header(title):
    """打印测试标题"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")


def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"[{status}] {test_name}")
    if message:
        print(f"      {message}")


def utc_now():
    """获取当前UTC时间"""
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 测试1: 学生画像数据结构
# ============================================================
def test_student_profile() -> bool:
    """测试学生画像数据结构"""
    print_header("测试1: 学生画像数据结构")
    
    try:
        # 创建学生画像
        profile = StudentProfile(
            user_id="test_user_001",
            version=1,
            course="database_system",
            dimensions={
                "专业与年级": DimensionValue(
                    value="计算机科学 / 大二",
                    confidence=0.85,
                    updated_at=utc_now(),
                    evidence="学生自我介绍"
                ),
                "知识基础": DimensionValue(
                    value="中级",
                    confidence=0.75,
                    updated_at=utc_now(),
                    evidence="已完成SQL基础"
                ),
                "易错点": DimensionValue(
                    value=["函数依赖", "范式判断"],
                    confidence=0.8,
                    updated_at=utc_now(),
                    evidence="历史答题数据分析"
                ),
            },
            completion=37.5,
            total_learning_time=120,
            total_questions=30,
            correct_rate=68.5,
            weak_points=["函数依赖", "范式判断"],
            strong_points=["SQL基础"],
            created_at=utc_now(),
            updated_at=utc_now(),
            last_active_at=utc_now(),
        )
        
        # 验证字段
        assert profile.user_id == "test_user_001"
        assert profile.version == 1
        assert "专业与年级" in profile.dimensions
        assert profile.dimensions["专业与年级"].value == "计算机科学 / 大二"
        assert len(profile.dimensions["易错点"].value) == 2
        
        # 验证JSON序列化
        json_str = profile.model_dump_json(indent=2)
        assert "test_user_001" in json_str
        assert "专业与年级" in json_str
        
        print_result("创建学生画像", True, f"包含{len(profile.dimensions)}个维度")
        
        # 验证JSON反序列化
        profile_dict = profile.model_dump()
        restored = StudentProfile(**profile_dict)
        assert restored.user_id == profile.user_id
        
        print_result("JSON序列化/反序列化", True)
        
        return True
        
    except Exception as e:
        print_result("学生画像测试", False, str(e))
        return False


# ============================================================
# 测试2: 学习活动数据结构
# ============================================================
def test_learning_activity() -> bool:
    """测试学习活动数据结构"""
    print_header("测试2: 学习活动数据结构")
    
    try:
        # 创建学习活动
        activity = LearningActivity(
            user_id="test_user_001",
            activity_type="read_document",
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc_06_normal_form",
            resource_title="数据库范式详解",
            topic="第三范式",
            started_at=utc_now(),
            ended_at=utc_now(),
            duration_seconds=1500,
            interaction_count=5,
            scroll_depth=0.85,
            completion_rate=1.0,
            understanding_level=0.75,
            difficulty_rating=3.0,
        )
        
        # 验证字段
        assert activity.user_id == "test_user_001"
        assert activity.activity_type == "read_document"
        assert activity.resource_type == ResourceType.DOCUMENT
        assert activity.duration_seconds == 1500
        
        print_result("创建学习活动", True, f"活动类型: {activity.activity_type}")
        
        # 测试不同的活动类型
        activity2 = LearningActivity(
            user_id="test_user_001",
            activity_type="view_mindmap",
            resource_type=ResourceType.MINDMAP,
            resource_title="数据库知识图谱",
            topic="索引",
            started_at=utc_now(),
        )
        assert activity2.resource_type == ResourceType.MINDMAP
        
        print_result("创建不同类型活动", True)
        
        return True
        
    except Exception as e:
        print_result("学习活动测试", False, str(e))
        return False


# ============================================================
# 测试3: 学习会话数据结构
# ============================================================
def test_learning_session() -> bool:
    """测试学习会话数据结构"""
    print_header("测试3: 学习会话数据结构")
    
    try:
        # 创建学习活动列表
        activities = [
            LearningActivity(
                user_id="test_user_001",
                activity_type="read_document",
                resource_type=ResourceType.DOCUMENT,
                topic="第一范式",
                started_at=utc_now(),
                duration_seconds=600,
            ),
            LearningActivity(
                user_id="test_user_001",
                activity_type="practice_sql",
                resource_type=ResourceType.PRACTICE,
                topic="第一范式",
                started_at=utc_now(),
                duration_seconds=900,
            ),
        ]
        
        # 创建学习会话
        session = LearningSession(
            session_id="session_test_001",
            user_id="test_user_001",
            started_at=utc_now(),
            ended_at=utc_now(),
            total_duration_seconds=1500,
            activity_count=2,
            activities=activities,
            topics_covered=["第一范式"],
            focus_score=0.85,
            learning_efficiency=0.78,
        )
        
        # 验证
        assert session.session_id == "session_test_001"
        assert len(session.activities) == 2
        assert session.total_duration_seconds == 1500
        
        print_result("创建学习会话", True, f"包含{len(session.activities)}个活动")
        
        return True
        
    except Exception as e:
        print_result("学习会话测试", False, str(e))
        return False


# ============================================================
# 测试4: 答题记录数据结构
# ============================================================
def test_answer_record() -> bool:
    """测试答题记录数据结构"""
    print_header("测试4: 答题记录数据结构")
    
    try:
        # 创建答题记录
        answer = AnswerRecord(
            user_id="test_user_001",
            question_id="q_2nf_judge_01",
            question_text="在第二范式中，非主属性必须完全函数依赖于主键。",
            question_type=QuestionType.TRUE_FALSE,
            topic="第二范式",
            difficulty=0.6,
            user_answer="正确",
            correct_answer="正确",
            is_correct=AnswerResult.CORRECT,
            answered_at=utc_now(),
            time_spent_seconds=45,
            score=100.0,
            explanation="第二范式确实要求非主属性完全函数依赖于主键。",
        )
        
        # 验证
        assert answer.user_id == "test_user_001"
        assert answer.question_type == QuestionType.TRUE_FALSE
        assert answer.is_correct == AnswerResult.CORRECT
        assert answer.score == 100.0
        
        print_result("创建答题记录", True, f"结果: {answer.is_correct.value}")
        
        # 创建错误答案记录
        wrong_answer = AnswerRecord(
            user_id="test_user_001",
            question_id="q_3nf_choice_01",
            question_text="以下哪个不是第三范式的特性?",
            question_type=QuestionType.SINGLE_CHOICE,
            topic="第三范式",
            difficulty=0.7,
            user_answer="B",
            correct_answer="C",
            is_correct=AnswerResult.INCORRECT,
            answered_at=utc_now(),
            time_spent_seconds=120,
            score=0.0,
        )
        assert wrong_answer.is_correct == AnswerResult.INCORRECT
        
        print_result("创建错误答题记录", True)
        
        return True
        
    except Exception as e:
        print_result("答题记录测试", False, str(e))
        return False


# ============================================================
# 测试5: 测验记录数据结构
# ============================================================
def test_quiz_attempt() -> bool:
    """测试测验记录数据结构"""
    print_header("测试5: 测验记录数据结构")
    
    try:
        # 创建答题列表
        answers = [
            AnswerRecord(
                user_id="test_user_001",
                question_id=f"q_{i}",
                question_text=f"测试题目{i}",
                question_type=QuestionType.SINGLE_CHOICE,
                topic="函数依赖",
                user_answer="A",
                correct_answer="A",
                is_correct=AnswerResult.CORRECT if i % 3 != 0 else AnswerResult.INCORRECT,
                answered_at=utc_now(),
                score=100.0 if i % 3 != 0 else 0.0,
            )
            for i in range(5)
        ]
        
        # 创建测验尝试
        attempt = QuizAttempt(
            attempt_id="quiz_test_001",
            user_id="test_user_001",
            quiz_title="函数依赖单元测验",
            quiz_type="practice",
            topics=["函数依赖"],
            started_at=utc_now(),
            submitted_at=utc_now(),
            total_time_seconds=600,
            answers=answers,
            total_questions=5,
            correct_count=3,
            incorrect_count=2,
            skipped_count=0,
            score=60.0,
            correct_rate=60.0,
            weak_points=["部分函数依赖"],
            strong_points=["完全函数依赖判断"],
        )
        
        # 验证
        assert attempt.attempt_id == "quiz_test_001"
        assert attempt.total_questions == 5
        assert attempt.correct_count == 3
        assert attempt.score == 60.0
        
        print_result("创建测验记录", True, f"正确率: {attempt.correct_rate}%")
        
        return True
        
    except Exception as e:
        print_result("测验记录测试", False, str(e))
        return False


# ============================================================
# 测试6: 知识点掌握度数据结构
# ============================================================
def test_topic_mastery() -> bool:
    """测试知识点掌握度数据结构"""
    print_header("测试6: 知识点掌握度数据结构")
    
    try:
        # 创建知识点掌握度
        mastery = TopicMastery(
            user_id="test_user_001",
            course="database_system",
            topic="函数依赖",
            mastery_level=0.65,
            confidence=0.8,
            total_attempts=10,
            correct_attempts=7,
            historical_correct_rate=70.0,
            trend="improving",
            last_attempt_at=utc_now(),
            attempts_history=[
                {"attempt_at": "2025-01-10", "is_correct": True},
                {"attempt_at": "2025-01-12", "is_correct": False},
                {"attempt_at": "2025-01-15", "is_correct": True},
            ],
            recommended_action="加强练习",
            priority=3,
        )
        
        # 验证
        assert mastery.topic == "函数依赖"
        assert mastery.mastery_level == 0.65
        assert mastery.trend == "improving"
        assert mastery.priority == 3
        
        print_result("创建知识点掌握度", True, f"掌握度: {mastery.mastery_level:.0%}")
        
        return True
        
    except Exception as e:
        print_result("知识点掌握度测试", False, str(e))
        return False


# ============================================================
# 测试7: 学习记录存储服务
# ============================================================
def test_learning_record_store() -> bool:
    """测试学习记录存储服务"""
    print_header("测试7: 学习记录存储服务")
    
    store = LearningRecordStore()
    test_user = "test_user_profile"
    
    try:
        # 保存学习活动
        activity = LearningActivity(
            user_id=test_user,
            activity_type="read_document",
            resource_type=ResourceType.DOCUMENT,
            resource_title="数据库范式详解",
            topic="第一范式",
            started_at=utc_now(),
            ended_at=utc_now(),
            duration_seconds=600,
        )
        saved_activity = store.save_activity(activity)
        
        print_result("保存学习活动", True, f"ID: {saved_activity.activity_id}")
        
        # 读取学习活动
        retrieved = store.get_activity(test_user, saved_activity.activity_id)
        assert retrieved is not None
        assert retrieved.activity_id == saved_activity.activity_id
        
        print_result("读取学习活动", True)
        
        # 获取用户活动列表
        activities = store.get_user_activities(test_user)
        assert len(activities) > 0
        
        print_result("获取活动列表", True, f"共{len(activities)}条")
        
        # 保存学习会话
        session = LearningSession(
            session_id=f"session_{utc_now()[:10]}",
            user_id=test_user,
            started_at=utc_now(),
            ended_at=utc_now(),
            total_duration_seconds=600,
            activity_count=1,
            topics_covered=["第一范式"],
        )
        saved_session = store.save_session(session)
        
        print_result("保存学习会话", True, f"ID: {saved_session.session_id}")
        
        # 获取用户会话
        sessions = store.get_user_sessions(test_user)
        assert len(sessions) > 0
        
        print_result("获取会话列表", True, f"共{len(sessions)}条")
        
        # 计算统计
        stats = store.calculate_statistics(test_user, period_type="daily")
        assert stats.total_activities > 0
        
        print_result("计算学习统计", True, f"今日活动: {stats.total_activities}次")
        
        # 清理测试数据
        count = store.clear_user_data(test_user)
        
        print_result("清理测试数据", True, f"删除{count}个文件")
        
        return True
        
    except Exception as e:
        print_result("学习记录存储测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试8: 答题记录存储服务
# ============================================================
def test_answer_record_store() -> bool:
    """测试答题记录存储服务"""
    print_header("测试8: 答题记录存储服务")
    
    store = AnswerRecordStore()
    test_user = "test_user_profile"
    
    try:
        # 保存答题记录
        answer = AnswerRecord(
            user_id=test_user,
            question_id="q_test_001",
            question_text="第一范式要求每个属性都是原子的。",
            question_type=QuestionType.TRUE_FALSE,
            topic="第一范式",
            difficulty=0.5,
            user_answer="正确",
            correct_answer="正确",
            is_correct=AnswerResult.CORRECT,
            answered_at=utc_now(),
            time_spent_seconds=30,
            score=100.0,
        )
        saved_answer = store.save_answer(answer)
        
        print_result("保存答题记录", True, f"ID: {saved_answer.record_id}")
        
        # 读取答题记录
        retrieved = store.get_answer(test_user, saved_answer.record_id)
        assert retrieved is not None
        assert retrieved.record_id == saved_answer.record_id
        
        print_result("读取答题记录", True)
        
        # 获取用户答题列表
        answers = store.get_user_answers(test_user)
        assert len(answers) > 0
        
        print_result("获取答题列表", True, f"共{len(answers)}条")
        
        # 获取知识点掌握度
        mastery = store.get_topic_mastery(test_user, "第一范式")
        assert mastery is not None
        assert mastery.topic == "第一范式"
        
        print_result("获取知识点掌握度", True, f"掌握度: {mastery.mastery_level:.0%}")
        
        # 获取用户统计
        stats = store.get_user_stats(test_user)
        assert stats["total_questions"] > 0
        
        print_result("获取答题统计", True, f"正确率: {stats['correct_rate']}%")
        
        # 获取薄弱点
        weak_points = store.get_weak_points(test_user)
        
        print_result("获取薄弱知识点", True, f"共{len(weak_points)}个")
        
        # 清理测试数据
        count = store.clear_user_data(test_user)
        
        print_result("清理测试数据", True, f"删除{count}个文件")
        
        return True
        
    except Exception as e:
        print_result("答题记录存储测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# 测试9: 存储配置验证
# ============================================================
def test_storage_config() -> bool:
    """测试存储配置"""
    print_header("测试9: 存储配置验证")
    
    try:
        # 验证目录配置
        assert StorageConfig.DATA_DIR == "data"
        assert StorageConfig.PROFILES_DIR == "profiles"
        assert StorageConfig.LEARNING_DIR == "learning"
        assert StorageConfig.ANSWERS_DIR == "answers"
        assert StorageConfig.TOPICS_DIR == "topics"
        
        print_result("目录配置正确", True)
        
        # 验证路径生成
        profile_path = StorageConfig.get_profile_path("user123")
        assert "profiles" in profile_path
        assert "user123" in profile_path
        
        print_result("路径生成正确", True, profile_path)
        
        return True
        
    except Exception as e:
        print_result("存储配置测试", False, str(e))
        return False


# ============================================================
# 主函数
# ============================================================
def main() -> None:
    """运行所有测试"""
    print("\n" + "="*70)
    print(" 学生画像、学习记录、答题记录数据结构测试")
    print("="*70)
    
    tests = [
        ("学生画像", test_student_profile),
        ("学习活动", test_learning_activity),
        ("学习会话", test_learning_session),
        ("答题记录", test_answer_record),
        ("测验记录", test_quiz_attempt),
        ("知识点掌握度", test_topic_mastery),
        ("学习记录存储", test_learning_record_store),
        ("答题记录存储", test_answer_record_store),
        ("存储配置", test_storage_config),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_result(name, False, f"异常: {e}")
            results.append((name, False))
    
    # 打印测试汇总
    print_header("测试汇总")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  [{status}] {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n所有测试通过！数据结构设计完整正确。")
    else:
        print(f"\n有 {total - passed} 个测试失败，请检查上述错误。")


if __name__ == "__main__":
    main()
