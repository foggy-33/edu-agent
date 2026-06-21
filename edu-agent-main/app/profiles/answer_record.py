"""答题记录存储服务"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings
from app.profiles.data_structures import (
    AnswerRecord,
    AnswerResult,
    QuestionType,
    QuizAttempt,
    StorageConfig,
    TopicMastery,
)


class AnswerRecordStore:
    """答题记录存储器"""
    
    def __init__(self) -> None:
        self.base_dir = Path(get_settings().profile_data_dir).parent / StorageConfig.ANSWERS_DIR
        self.topics_dir = Path(get_settings().profile_data_dir).parent / StorageConfig.TOPICS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.topics_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
    
    def _user_dir(self, user_id: str) -> Path:
        """获取用户答题记录目录"""
        safe_id = self._safe_id(user_id)
        user_dir = self.base_dir / safe_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _user_topics_dir(self, user_id: str) -> Path:
        """获取用户知识点掌握度目录"""
        safe_id = self._safe_id(user_id)
        user_dir = self.topics_dir / safe_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    @staticmethod
    def _safe_id(user_id: str) -> str:
        """安全的用户ID"""
        import re
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", user_id)[:80] or "anonymous"
        return safe
    
    @staticmethod
    def _now() -> str:
        """获取当前UTC时间"""
        return datetime.now(timezone.utc).isoformat()
    
    # ==================== 答题记录 ====================
    
    def save_answer(self, answer: AnswerRecord) -> AnswerRecord:
        """保存答题记录"""
        answer.record_id = answer.record_id or f"ans_{uuid.uuid4().hex[:12]}"
        if not answer.answered_at:
            answer.answered_at = self._now()
        
        user_dir = self._user_dir(answer.user_id)
        path = user_dir / f"{answer.record_id}.json"
        
        with self._lock:
            path.write_text(answer.model_dump_json(indent=2), encoding="utf-8")
        
        # 更新知识点掌握度
        self._update_topic_mastery(answer)
        
        return answer
    
    def get_answer(self, user_id: str, record_id: str) -> AnswerRecord | None:
        """获取答题记录"""
        user_dir = self._user_dir(user_id)
        path = user_dir / f"{record_id}.json"
        
        if not path.exists():
            return None
        
        with self._lock:
            data = json.loads(path.read_text(encoding="utf-8"))
        
        return AnswerRecord(**data)
    
    def get_user_answers(
        self,
        user_id: str,
        limit: int = 100,
        topic: str = "",
        question_type: QuestionType | None = None,
        is_correct: AnswerResult | None = None,
    ) -> list[AnswerRecord]:
        """获取用户答题记录列表"""
        user_dir = self._user_dir(user_id)
        answers = []
        
        with self._lock:
            for path in sorted(user_dir.glob("ans_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    answer = AnswerRecord(**data)
                    
                    # 过滤
                    if topic and topic not in answer.topic:
                        continue
                    if question_type and answer.question_type != question_type:
                        continue
                    if is_correct and answer.is_correct != is_correct:
                        continue
                    
                    answers.append(answer)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return answers
    
    def _update_topic_mastery(self, answer: AnswerRecord) -> None:
        """更新知识点掌握度"""
        if not answer.topic:
            return
        
        user_dir = self._user_topics_dir(answer.user_id)
        path = user_dir / f"{answer.topic}.json"
        
        mastery: dict[str, Any] = {}
        if path.exists():
            with self._lock:
                mastery = json.loads(path.read_text(encoding="utf-8"))
        
        # 更新统计数据
        mastery["user_id"] = answer.user_id
        mastery["course"] = answer.course
        mastery["topic"] = answer.topic
        mastery["total_attempts"] = mastery.get("total_attempts", 0) + 1
        
        if answer.is_correct == AnswerResult.CORRECT:
            mastery["correct_attempts"] = mastery.get("correct_attempts", 0) + 1
        
        # 计算历史正确率
        total = mastery["total_attempts"]
        correct = mastery["correct_attempts"]
        mastery["historical_correct_rate"] = round(correct / total * 100, 1) if total > 0 else 0.0
        
        # 更新尝试历史（保留最近10次）
        history = mastery.get("attempts_history", [])
        history.append({
            "attempt_at": answer.answered_at,
            "is_correct": answer.is_correct == AnswerResult.CORRECT,
            "difficulty": answer.difficulty,
        })
        mastery["attempts_history"] = history[-10:]
        
        # 计算掌握度（考虑难度权重）
        mastery["mastery_level"] = self._calculate_mastery(mastery)
        
        # 计算趋势
        mastery["trend"] = self._calculate_trend(mastery.get("attempts_history", []))
        
        # 置信度（基于尝试次数）
        mastery["confidence"] = min(0.95, 0.3 + 0.07 * total)
        
        # 优先级（基于错误频率和趋势）
        mastery["priority"] = self._calculate_priority(mastery)
        
        # 推荐行动
        mastery["recommended_action"] = self._get_recommended_action(mastery)
        mastery["last_attempt_at"] = answer.answered_at
        
        with self._lock:
            path.write_text(json.dumps(mastery, indent=2), encoding="utf-8")
    
    @staticmethod
    def _calculate_mastery(mastery: dict[str, Any]) -> float:
        """计算掌握度"""
        total = mastery.get("total_attempts", 0)
        correct = mastery.get("correct_attempts", 0)
        
        if total == 0:
            return 0.0
        
        # 基础正确率
        base_rate = correct / total
        
        # 考虑历史权重（最近的表现更重要）
        history = mastery.get("attempts_history", [])
        if len(history) >= 3:
            recent = history[-3:]
            recent_rate = sum(1 for h in recent if h.get("is_correct")) / len(recent)
            # 加权平均
            base_rate = base_rate * 0.4 + recent_rate * 0.6
        
        # 考虑难度
        difficulties = [h.get("difficulty", 0.5) for h in history]
        if difficulties:
            avg_difficulty = sum(difficulties) / len(difficulties)
            # 高难度题答对应该提升掌握度
            if avg_difficulty > 0.6 and base_rate > 0.7:
                base_rate = min(1.0, base_rate + 0.1)
        
        return round(min(1.0, base_rate), 3)
    
    @staticmethod
    def _calculate_trend(history: list[dict[str, Any]]) -> str:
        """计算趋势"""
        if len(history) < 3:
            return "stable"
        
        recent = history[-3:]
        older = history[:-3][-3:] if len(history) > 3 else history[:-3]
        
        if not older:
            return "stable"
        
        recent_rate = sum(1 for h in recent if h.get("is_correct")) / len(recent)
        older_rate = sum(1 for h in older if h.get("is_correct")) / len(older)
        
        diff = recent_rate - older_rate
        
        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        return "stable"
    
    @staticmethod
    def _calculate_priority(mastery: dict[str, Any]) -> int:
        """计算优先级"""
        priority = 0
        
        # 错误次数多 -> 高优先级
        error_rate = 1 - mastery.get("historical_correct_rate", 50) / 100
        priority += int(error_rate * 5)
        
        # 趋势下降 -> 高优先级
        if mastery.get("trend") == "declining":
            priority += 3
        elif mastery.get("trend") == "improving":
            priority -= 1
        
        # 尝试次数少但正确率低 -> 中优先级
        total = mastery.get("total_attempts", 0)
        if total < 3 and mastery.get("historical_correct_rate", 50) < 60:
            priority += 2
        
        return max(0, min(10, priority))
    
    @staticmethod
    def _get_recommended_action(mastery: dict[str, Any]) -> str:
        """获取推荐行动"""
        rate = mastery.get("historical_correct_rate", 0)
        trend = mastery.get("trend", "stable")
        total = mastery.get("total_attempts", 0)
        
        if rate >= 85 and trend != "declining":
            return "已熟练，继续保持"
        elif rate >= 70:
            return "加强练习巩固"
        elif rate >= 50:
            return "重点复习相关概念"
        elif total < 3:
            return "增加练习次数"
        else:
            return "需要系统学习该知识点"
    
    # ==================== 测验记录 ====================
    
    def save_quiz_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        """保存测验尝试"""
        if not attempt.attempt_id:
            attempt.attempt_id = f"quiz_{uuid.uuid4().hex[:12]}"
        
        if not attempt.started_at:
            attempt.started_at = self._now()
        
        user_dir = self._user_dir(attempt.user_id)
        path = user_dir / f"{attempt.attempt_id}.json"
        
        with self._lock:
            path.write_text(attempt.model_dump_json(indent=2), encoding="utf-8")
        
        return attempt
    
    def get_quiz_attempt(self, user_id: str, attempt_id: str) -> QuizAttempt | None:
        """获取测验尝试"""
        user_dir = self._user_dir(user_id)
        path = user_dir / f"{attempt_id}.json"
        
        if not path.exists():
            return None
        
        with self._lock:
            data = json.loads(path.read_text(encoding="utf-8"))
        
        return QuizAttempt(**data)
    
    def get_user_quiz_attempts(
        self,
        user_id: str,
        limit: int = 50,
        course: str = "",
        topics: list[str] | None = None,
    ) -> list[QuizAttempt]:
        """获取用户测验尝试列表"""
        user_dir = self._user_dir(user_id)
        attempts = []
        
        with self._lock:
            for path in sorted(user_dir.glob("quiz_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if course and data.get("course") != course:
                        continue
                    if topics:
                        attempt_topics = set(data.get("topics", []))
                        if not attempt_topics.intersection(set(topics)):
                            continue
                    attempts.append(QuizAttempt(**data))
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return attempts
    
    # ==================== 知识点掌握度 ====================
    
    def get_topic_mastery(self, user_id: str, topic: str) -> TopicMastery | None:
        """获取知识点掌握度"""
        user_dir = self._user_topics_dir(user_id)
        path = user_dir / f"{topic}.json"
        
        if not path.exists():
            return None
        
        with self._lock:
            data = json.loads(path.read_text(encoding="utf-8"))
        
        return TopicMastery(**data)
    
    def get_user_topics(self, user_id: str) -> list[TopicMastery]:
        """获取用户所有知识点掌握度"""
        user_dir = self._user_topics_dir(user_id)
        topics = []
        
        with self._lock:
            for path in user_dir.glob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    topics.append(TopicMastery(**data))
                except (json.JSONDecodeError, ValueError):
                    continue
        
        # 按优先级排序
        return sorted(topics, key=lambda t: t.priority, reverse=True)
    
    def get_weak_points(self, user_id: str, top_n: int = 5) -> list[str]:
        """获取薄弱知识点"""
        topics = self.get_user_topics(user_id)
        weak = [t.topic for t in topics if t.mastery_level < 0.6][:top_n]
        return weak
    
    def get_strong_points(self, user_id: str, top_n: int = 5) -> list[str]:
        """获取强项知识点"""
        topics = self.get_user_topics(user_id)
        strong = [t.topic for t in topics if t.mastery_level >= 0.8][:top_n]
        return strong
    
    # ==================== 统计分析 ====================
    
    def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """获取用户答题统计"""
        answers = self.get_user_answers(user_id, limit=10000)
        
        if not answers:
            return {
                "total_questions": 0,
                "correct_count": 0,
                "correct_rate": 0.0,
                "by_topic": {},
                "by_type": {},
            }
        
        # 总体统计
        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct == AnswerResult.CORRECT)
        
        # 按知识点统计
        by_topic: dict[str, dict[str, Any]] = {}
        for a in answers:
            if a.topic:
                if a.topic not in by_topic:
                    by_topic[a.topic] = {"total": 0, "correct": 0}
                by_topic[a.topic]["total"] += 1
                if a.is_correct == AnswerResult.CORRECT:
                    by_topic[a.topic]["correct"] += 1
        
        # 按题型统计
        by_type: dict[str, dict[str, Any]] = {}
        for a in answers:
            qtype = a.question_type.value
            if qtype not in by_type:
                by_type[qtype] = {"total": 0, "correct": 0}
            by_type[qtype]["total"] += 1
            if a.is_correct == AnswerResult.CORRECT:
                by_type[qtype]["correct"] += 1
        
        return {
            "total_questions": total,
            "correct_count": correct,
            "incorrect_count": total - correct,
            "correct_rate": round(correct / total * 100, 1) if total > 0 else 0.0,
            "by_topic": {
                topic: {
                    "total": stats["total"],
                    "correct": stats["correct"],
                    "rate": round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0.0,
                }
                for topic, stats in by_topic.items()
            },
            "by_type": {
                qtype: {
                    "total": stats["total"],
                    "correct": stats["correct"],
                    "rate": round(stats["correct"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0.0,
                }
                for qtype, stats in by_type.items()
            },
        }
    
    # ==================== 删除操作 ====================
    
    def delete_answer(self, user_id: str, record_id: str) -> bool:
        """删除答题记录"""
        user_dir = self._user_dir(user_id)
        path = user_dir / f"{record_id}.json"
        
        if path.exists():
            with self._lock:
                path.unlink()
            return True
        return False
    
    def clear_user_data(self, user_id: str) -> int:
        """清除用户所有答题数据，返回删除的文件数"""
        count = 0
        
        # 清除答题记录
        user_dir = self._user_dir(user_id)
        with self._lock:
            for path in user_dir.glob("*.json"):
                path.unlink()
                count += 1
        
        # 清除知识点数据
        topics_dir = self._user_topics_dir(user_id)
        with self._lock:
            for path in topics_dir.glob("*.json"):
                path.unlink()
                count += 1
        
        return count
