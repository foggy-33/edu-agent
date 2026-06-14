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

    def get(self, user_id: str) -> dict[str, Any] | None:
        path = self._path(user_id)
        if not path.exists():
            return None
        with self._lock:
            return json.loads(path.read_text(encoding="utf-8"))

    def save(self, user_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        path = self._path(user_id)
        with self._lock:
            path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        return profile

    def _path(self, user_id: str) -> Path:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", user_id)[:80] or "anonymous"
        return self.base_dir / f"{safe_id}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
