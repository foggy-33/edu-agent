from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings


class ProfileStore:
    def __init__(self) -> None:
        self.base_dir = Path(get_settings().profile_data_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def get(self, user_id: str, course: str | None = None) -> dict[str, Any] | None:
        if course:
            path = self._subject_path(user_id, course)
            if path.exists():
                return self._read(path)

            legacy = self._legacy_path(user_id)
            if legacy.exists():
                profile = self._read(legacy)
                if profile.get("course") == course or (course == "未分类画像" and not profile.get("course")):
                    profile.setdefault("course", "未分类画像")
                    return profile
            return None

        profiles = self.list(user_id)
        if not profiles:
            return None
        latest = self.get(user_id, profiles[0]["course"])
        if latest:
            return latest
        legacy = self._legacy_path(user_id)
        return self._read(legacy) if legacy.exists() else None

    def list(self, user_id: str) -> list[dict[str, Any]]:
        profiles: list[dict[str, Any]] = []
        user_dir = self._user_dir(user_id)
        if user_dir.exists():
            for path in user_dir.glob("*.json"):
                profile = self._read(path)
                if str(profile.get("course") or "未分类画像") == "未分类画像":
                    continue
                profiles.append(self._summary(profile))

        legacy = self._legacy_path(user_id)
        if legacy.exists():
            profile = self._read(legacy)
            course = str(profile.get("course") or "未分类画像")
            if course != "未分类画像" and not any(item["course"] == course for item in profiles):
                profile["course"] = course
                profiles.append(self._summary(profile))

        return sorted(profiles, key=lambda item: item.get("updated_at") or "", reverse=True)

    def save(self, user_id: str, course: str, profile: dict[str, Any]) -> dict[str, Any]:
        path = self._subject_path(user_id, course)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        return profile

    @staticmethod
    def _summary(profile: dict[str, Any]) -> dict[str, Any]:
        return {
            "course": profile.get("course", "未分类画像"),
            "version": profile.get("version", 0),
            "completion": profile.get("completion", 0),
            "updated_at": profile.get("updated_at"),
            "summary": profile.get("llm_context", {}).get("summary", ""),
            "radar_metrics": profile.get("radar_metrics", {}),
        }

    def _read(self, path: Path) -> dict[str, Any]:
        with self._lock:
            return json.loads(path.read_text(encoding="utf-8"))

    def _user_dir(self, user_id: str) -> Path:
        return self.base_dir / self._safe_name(user_id)

    def _subject_path(self, user_id: str, course: str) -> Path:
        return self._user_dir(user_id) / f"{self._safe_name(course)}.json"

    def _legacy_path(self, user_id: str) -> Path:
        return self.base_dir / f"{self._safe_name(user_id)}.json"

    @staticmethod
    def _safe_name(value: str) -> str:
        safe = re.sub(r"[^\w-]", "_", value, flags=re.UNICODE).strip("_")
        return safe[:80] or "unknown"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
