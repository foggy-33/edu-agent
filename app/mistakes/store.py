from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings


class MistakeStore:
    """错题本存储"""
    def __init__(self):
        self.base_dir = Path(get_settings().profile_data_dir) / "mistakes"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def add_mistake(self, user_id: str, course: str, record: dict[str, Any]) -> dict:
        """添加错题记录"""
        mistakes = self._load(user_id, course)
        record["last_mistake_at"] = datetime.now(timezone.utc).isoformat()
        
        existing = next(
            (m for m in mistakes if m.get("question") == record.get("question")),
            None
        )
        
        if existing:
            existing["mistake_count"] = existing.get("mistake_count", 1) + 1
            existing["last_mistake_at"] = record["last_mistake_at"]
            existing["student_answer"] = record.get("student_answer")
            existing["mastered"] = False
        else:
            record["mistake_count"] = 1
            record["review_count"] = 0
            record["mastered"] = False
            mistakes.append(record)
        
        self._save(user_id, course, mistakes)
        return record

    def list_mistakes(self, user_id: str, course: str, mastered: bool = False) -> list[dict]:
        """获取错题列表"""
        mistakes = self._load(user_id, course)
        if mastered:
            return [m for m in mistakes if m.get("mastered")]
        return [m for m in mistakes if not m.get("mastered")]

    def mark_mastered(self, user_id: str, course: str, question_id: str) -> None:
        """标记为已掌握"""
        mistakes = self._load(user_id, course)
        for m in mistakes:
            if m.get("question_id") == question_id or m.get("question") == question_id:
                m["mastered"] = True
                m["review_count"] = m.get("review_count", 0) + 1
                m["last_review_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._save(user_id, course, mistakes)

    def mark_mastered_any_course(self, user_id: str, question_id: str) -> None:
        """在所有课程中查找并标记为已掌握"""
        user_dir = self.base_dir / user_id.replace("/", "_").replace("\\", "_")
        if not user_dir.exists():
            return
        for course_file in user_dir.glob("*.json"):
            try:
                mistakes = json.loads(course_file.read_text(encoding="utf-8"))
                found = False
                for m in mistakes:
                    if m.get("question_id") == question_id or m.get("question") == question_id:
                        m["mastered"] = True
                        m["review_count"] = m.get("review_count", 0) + 1
                        m["last_review_at"] = datetime.now(timezone.utc).isoformat()
                        found = True
                        break
                if found:
                    course_file.write_text(json.dumps(mistakes, ensure_ascii=False), encoding="utf-8")
                    break
            except:
                continue

    def get_weak_topics(self, user_id: str, course: str, limit: int = 5) -> list[str]:
        """获取薄弱章节"""
        mistakes = self.list_mistakes(user_id, course)
        topic_counts = {}
        for m in mistakes:
            topic = m.get("chapter") or m.get("topic") or "综合"
            topic_counts[topic] = topic_counts.get(topic, 0) + m.get("mistake_count", 1)
        
        return [topic for topic, _ in sorted(topic_counts.items(), key=lambda x: -x[1])][:limit]

    def list_all_mistakes(self, user_id: str, mastered: bool = False) -> list[dict]:
        """获取用户所有课程的错题"""
        user_dir = self.base_dir / user_id.replace("/", "_").replace("\\", "_")
        if not user_dir.exists():
            return []
        all_mistakes = []
        for course_file in user_dir.glob("*.json"):
            try:
                mistakes = json.loads(course_file.read_text(encoding="utf-8"))
                for m in mistakes:
                    if m.get("mastered") == mastered:
                        m["course_name"] = course_file.stem
                        all_mistakes.append(m)
            except:
                continue
        return all_mistakes

    def get_mistake_stats(self, user_id: str) -> list[dict]:
        """获取按课程分类的错题统计"""
        user_dir = self.base_dir / user_id.replace("/", "_").replace("\\", "_")
        if not user_dir.exists():
            return []
        stats = []
        for course_file in user_dir.glob("*.json"):
            try:
                mistakes = json.loads(course_file.read_text(encoding="utf-8"))
                unmastered_count = sum(1 for m in mistakes if not m.get("mastered"))
                mastered_count = sum(1 for m in mistakes if m.get("mastered"))
                if unmastered_count > 0 or mastered_count > 0:
                    stats.append({
                        "course_name": course_file.stem,
                        "unmastered_count": unmastered_count,
                        "mastered_count": mastered_count,
                        "total_count": len(mistakes)
                    })
            except:
                continue
        return sorted(stats, key=lambda x: -x["unmastered_count"])

    def _load(self, user_id: str, course: str) -> list[dict]:
        path = self._path(user_id, course)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return []

    def _save(self, user_id: str, course: str, mistakes: list[dict]) -> None:
        path = self._path(user_id, course)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            path.write_text(json.dumps(mistakes, ensure_ascii=False, indent=2), encoding="utf-8")

    def _path(self, user_id: str, course: str) -> Path:
        safe_user = user_id.replace("/", "_").replace("\\", "_")
        safe_course = course.replace("/", "_").replace("\\", "_")
        return self.base_dir / safe_user / f"{safe_course}.json"
