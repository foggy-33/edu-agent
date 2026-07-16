from __future__ import annotations

import base64
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
                "onboarding_completed": False,
                "onboarding_profile": {},
            }
            data["users"][normalized] = user
            token = self._new_session(user)
            self._write(data)
        return {"token": token, "user": self._public_user(user)}

    def get_onboarding_status(self, username: str) -> dict[str, Any]:
        normalized = username.strip().lower()
        with self._lock:
            data = self._read()
            user = data["users"].get(normalized)
            if not user:
                raise AuthError("用户不存在")
            return {
                "onboarding_completed": user.get("onboarding_completed", False),
                "onboarding_profile": user.get("onboarding_profile", {}),
            }

    def save_onboarding_profile(self, username: str, profile: dict[str, Any]) -> dict[str, Any]:
        normalized = username.strip().lower()
        with self._lock:
            data = self._read()
            user = data["users"].get(normalized)
            if not user:
                raise AuthError("用户不存在")
            user["onboarding_profile"] = profile
            user["onboarding_completed"] = True
            user["onboarding_completed_at"] = self._now()
            self._write(data)
            return {
                "onboarding_completed": True,
                "onboarding_profile": profile,
            }

    def update_profile(self, username: str, profile_data: dict[str, Any]) -> dict[str, Any]:
        normalized = username.strip().lower()
        with self._lock:
            data = self._read()
            user = data["users"].get(normalized)
            if not user:
                raise AuthError("用户不存在")
            if "display_name" in profile_data and profile_data["display_name"]:
                user["display_name"] = str(profile_data["display_name"]).strip()[:30]
            if "avatar" in profile_data:
                avatar_value = profile_data["avatar"] or ""
                if avatar_value.startswith("data:image"):
                    avatar_value = self._save_avatar_file(normalized, avatar_value)
                user["avatar"] = avatar_value
            if "phone" in profile_data:
                user["phone"] = profile_data["phone"] or ""
            if "email" in profile_data:
                user["email"] = profile_data["email"] or ""
            if "school" in profile_data:
                user["school"] = profile_data["school"] or ""
            if "major" in profile_data:
                user["major"] = profile_data["major"] or ""
            if "grade_level" in profile_data:
                user["grade_level"] = profile_data["grade_level"] or ""
            if "learning_goal" in profile_data:
                user["learning_goal"] = profile_data["learning_goal"] or ""
            self._write(data)
            return self._public_user(user)

    def _save_avatar_file(self, username: str, data_url: str) -> str:
        avatar_dir = Path(get_settings().avatar_dir)
        avatar_dir.mkdir(parents=True, exist_ok=True)
        header, encoded = data_url.split(",", 1)
        ext = "png"
        if "jpeg" in header or "jpg" in header:
            ext = "jpg"
        elif "webp" in header:
            ext = "webp"
        elif "gif" in header:
            ext = "gif"
        filename = f"{username}.{ext}"
        filepath = avatar_dir / filename
        filepath.write_bytes(base64.b64decode(encoded))
        return f"/api/avatars/{filename}"

    def get_profile(self, username: str) -> dict[str, Any]:
        normalized = username.strip().lower()
        with self._lock:
            data = self._read()
            user = data["users"].get(normalized)
            if not user:
                raise AuthError("用户不存在")
            return self._public_user(user)

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        normalized = username.strip().lower()
        with self._lock:
            data = self._read()
            user = data["users"].get(normalized)
            if not user:
                return None
            return dict(user)

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
    def _public_user(user: dict[str, Any]) -> dict[str, Any]:
        return {
            "username": user["username"],
            "display_name": user["display_name"],
            "created_at": user["created_at"],
            "onboarding_completed": user.get("onboarding_completed", False),
            "avatar": user.get("avatar", ""),
            "phone": user.get("phone", ""),
            "email": user.get("email", ""),
            "school": user.get("school", ""),
            "major": user.get("major", ""),
            "grade_level": user.get("grade_level", ""),
            "learning_goal": user.get("learning_goal", ""),
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
