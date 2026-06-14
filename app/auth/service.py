from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(self) -> None:
        self.path = Path(get_settings().user_data_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def register(self, username: str, display_name: str, password: str) -> dict[str, Any]:
        normalized = username.strip().lower()
        self._validate_credentials(normalized, password)
        if not display_name.strip():
            raise AuthError("显示名称不能为空")

        with self._lock:
            data = self._read()
            if normalized in data["users"]:
                raise AuthError("该用户名已被注册")
            salt = secrets.token_hex(16)
            user = {
                "username": normalized,
                "display_name": display_name.strip()[:30],
                "salt": salt,
                "password_hash": self._hash_password(password, salt),
                "created_at": self._now(),
                "sessions": [],
            }
            data["users"][normalized] = user
            token = self._new_session(user)
            self._write(data)
        return {"token": token, "user": self._public_user(user)}

    def login(self, username: str, password: str) -> dict[str, Any]:
        normalized = username.strip().lower()
        with self._lock:
            data = self._read()
            user = data["users"].get(normalized)
            if not user or not hmac.compare_digest(user["password_hash"], self._hash_password(password, user["salt"])):
                raise AuthError("用户名或密码错误")
            token = self._new_session(user)
            self._write(data)
        return {"token": token, "user": self._public_user(user)}

    def authenticate(self, token: str) -> dict[str, str]:
        token_hash = self._hash_token(token)
        with self._lock:
            for user in self._read()["users"].values():
                if any(hmac.compare_digest(item, token_hash) for item in user.get("sessions", [])):
                    return self._public_user(user)
        raise AuthError("登录状态已失效，请重新登录")

    def logout(self, token: str) -> None:
        token_hash = self._hash_token(token)
        with self._lock:
            data = self._read()
            for user in data["users"].values():
                sessions = user.get("sessions", [])
                if token_hash in sessions:
                    user["sessions"] = [item for item in sessions if item != token_hash]
                    self._write(data)
                    return

    def _validate_credentials(self, username: str, password: str) -> None:
        if not re.fullmatch(r"[a-z0-9_]{3,24}", username):
            raise AuthError("用户名需为 3-24 位字母、数字或下划线")
        if len(password) < 8:
            raise AuthError("密码至少需要 8 位")

    def _new_session(self, user: dict[str, Any]) -> str:
        token = secrets.token_urlsafe(32)
        user["sessions"] = [*user.get("sessions", [])[-4:], self._hash_token(token)]
        return token

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000).hex()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _public_user(user: dict[str, Any]) -> dict[str, str]:
        return {
            "username": user["username"],
            "display_name": user["display_name"],
            "created_at": user["created_at"],
        }

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"users": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
