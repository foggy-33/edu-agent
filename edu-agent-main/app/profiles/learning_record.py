"""学习记录存储服务"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings
from app.profiles.data_structures import (
    LearningActivity,
    LearningSession,
    LearningStatistics,
    StorageConfig,
)


class LearningRecordStore:
    """学习记录存储器"""
    
    def __init__(self) -> None:
        self.base_dir = Path(get_settings().profile_data_dir).parent / StorageConfig.LEARNING_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
    
    def _user_dir(self, user_id: str) -> Path:
        """获取用户学习记录目录"""
        safe_id = self._safe_id(user_id)
        user_dir = self.base_dir / safe_id
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
    
    # ==================== 学习活动 ====================
    
    def save_activity(self, activity: LearningActivity) -> LearningActivity:
        """保存学习活动"""
        activity.activity_id = activity.activity_id or f"act_{uuid.uuid4().hex[:12]}"
        if not activity.started_at:
            activity.started_at = self._now()
        
        user_dir = self._user_dir(activity.user_id)
        path = user_dir / f"{activity.activity_id}.json"
        
        with self._lock:
            path.write_text(activity.model_dump_json(indent=2), encoding="utf-8")
        
        # 更新会话统计
        self._update_session_stats(activity)
        
        return activity
    
    def get_activity(self, user_id: str, activity_id: str) -> LearningActivity | None:
        """获取学习活动"""
        user_dir = self._user_dir(user_id)
        path = user_dir / f"{activity_id}.json"
        
        if not path.exists():
            return None
        
        with self._lock:
            data = json.loads(path.read_text(encoding="utf-8"))
        
        return LearningActivity(**data)
    
    def get_user_activities(
        self,
        user_id: str,
        limit: int = 100,
        topic: str = "",
        activity_type: str = "",
    ) -> list[LearningActivity]:
        """获取用户学习活动列表"""
        user_dir = self._user_dir(user_id)
        activities = []
        
        with self._lock:
            for path in sorted(user_dir.glob("act_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    activity = LearningActivity(**data)
                    
                    # 过滤
                    if topic and topic not in activity.topic:
                        continue
                    if activity_type and activity_type != activity.activity_type:
                        continue
                    
                    activities.append(activity)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return activities
    
    def _update_session_stats(self, activity: LearningActivity) -> None:
        """更新会话统计"""
        session_id = f"session_{activity.started_at[:10]}"
        session_path = self._user_dir(activity.user_id) / f"{session_id}.json"
        
        session: dict[str, Any] = {}
        if session_path.exists():
            with self._lock:
                session = json.loads(session_path.read_text(encoding="utf-8"))
        
        # 更新会话数据
        session["session_id"] = session_id
        session["user_id"] = activity.user_id
        session["course"] = activity.course
        session["started_at"] = session.get("started_at") or activity.started_at
        session["ended_at"] = activity.ended_at or activity.started_at
        session["topics_covered"] = list(set(session.get("topics_covered", []) + [activity.topic]))
        
        # 活动列表
        activities = session.get("activities", [])
        activities.append(activity.activity_id)
        session["activities"] = activities[-50:]  # 保留最近50个
        session["activity_count"] = len(activities)
        
        with self._lock:
            session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    
    # ==================== 学习会话 ====================
    
    def save_session(self, session: LearningSession) -> LearningSession:
        """保存学习会话"""
        if not session.session_id:
            session.session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        user_dir = self._user_dir(session.user_id)
        path = user_dir / f"{session.session_id}.json"
        
        with self._lock:
            path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
        
        return session
    
    def get_session(self, user_id: str, session_id: str) -> LearningSession | None:
        """获取学习会话"""
        user_dir = self._user_dir(user_id)
        path = user_dir / f"{session_id}.json"
        
        if not path.exists():
            return None
        
        with self._lock:
            data = json.loads(path.read_text(encoding="utf-8"))
        
        return LearningSession(**data)
    
    def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        course: str = "",
    ) -> list[LearningSession]:
        """获取用户学习会话列表"""
        user_dir = self._user_dir(user_id)
        sessions = []
        
        with self._lock:
            for path in sorted(user_dir.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if course and data.get("course") != course:
                        continue
                    sessions.append(LearningSession(**data))
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return sessions
    
    # ==================== 学习统计 ====================
    
    def calculate_statistics(
        self,
        user_id: str,
        period_type: str = "weekly",
        period_start: str = "",
        period_end: str = "",
    ) -> LearningStatistics:
        """计算学习统计"""
        if not period_start:
            now = datetime.now(timezone.utc)
            if period_type == "daily":
                period_start = now.replace(hour=0, minute=0, second=0).isoformat()
            elif period_type == "weekly":
                period_start = (now.replace(hour=0, minute=0, second=0) - datetime.timedelta(days=7)).isoformat()
            else:  # monthly
                period_start = (now.replace(hour=0, minute=0, second=0) - datetime.timedelta(days=30)).isoformat()
            period_end = now.isoformat()
        
        activities = self.get_user_activities(user_id, limit=1000)
        
        # 过滤时间范围
        filtered = [
            a for a in activities
            if period_start <= a.started_at <= period_end
        ]
        
        # 统计
        total_time = sum(a.duration_seconds for a in filtered) // 60
        active_days = len(set(a.started_at[:10] for a in filtered))
        
        activities_by_type: dict[str, int] = {}
        topics = []
        for a in filtered:
            activities_by_type[a.activity_type] = activities_by_type.get(a.activity_type, 0) + 1
            if a.topic:
                topics.append(a.topic)
        
        stats = LearningStatistics(
            user_id=user_id,
            course="database_system",
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            total_learning_time=total_time,
            active_days=active_days,
            average_session_length=total_time // max(active_days, 1),
            total_activities=len(filtered),
            activities_by_type=activities_by_type,
            topics_covered=list(set(topics)),
            resources_accessed=len(set(a.resource_id for a in filtered if a.resource_id)),
        )
        
        return stats
    
    # ==================== 删除操作 ====================
    
    def delete_activity(self, user_id: str, activity_id: str) -> bool:
        """删除学习活动"""
        user_dir = self._user_dir(user_id)
        path = user_dir / f"{activity_id}.json"
        
        if path.exists():
            with self._lock:
                path.unlink()
            return True
        return False
    
    def clear_user_data(self, user_id: str) -> int:
        """清除用户所有学习数据，返回删除的文件数"""
        user_dir = self._user_dir(user_id)
        count = 0
        
        with self._lock:
            for path in user_dir.glob("*.json"):
                path.unlink()
                count += 1
        
        return count
