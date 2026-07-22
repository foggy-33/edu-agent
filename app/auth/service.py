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
        settings = get_settings()
        self.path = Path(settings.user_data_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self.admin_username = settings.admin_username.strip().lower()
        self.admin_password = settings.admin_password
        self.admin_display_name = settings.admin_display_name.strip() or "系统管理员"
        self._ensure_admin_user()

    def register(self, username: str, display_name: str, password: str) -> dict[str, Any]:
        normalized = username.strip().lower()
        self._validate_credentials(normalized, password)
        if not display_name.strip():
            raise AuthError("显示名称不能为空")
        if self.admin_username and normalized == self.admin_username:
            raise AuthError("该用户名为系统管理员保留账号")

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
                "role": "user",
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

    def update_avatar_file(self, username: str, content: bytes, content_type: str) -> dict[str, Any]:
        normalized = username.strip().lower()
        allowed_types = {
            "image/jpeg": ("jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
            "image/png": ("png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
            "image/webp": ("webp", lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
        }
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type not in allowed_types:
            raise AuthError("仅支持 JPG、PNG 和 WebP 头像")
        if not content or len(content) > 10 * 1024 * 1024:
            raise AuthError("头像文件不能为空且不能超过 10 MB")
        extension, signature_matches = allowed_types[media_type]
        if not signature_matches(content):
            raise AuthError("头像文件内容与图片格式不匹配")

        avatar_dir = Path(get_settings().avatar_dir)
        avatar_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(content).hexdigest()[:16]
        filename = f"{normalized}-{digest}.{extension}"
        filepath = avatar_dir / filename

        with self._lock:
            data = self._read()
            user = data["users"].get(normalized)
            if not user:
                raise AuthError("用户不存在")
            previous_avatar = str(user.get("avatar", ""))
            if not filepath.exists():
                temporary = avatar_dir / f".{filename}.tmp"
                temporary.write_bytes(content)
                temporary.replace(filepath)
            user["avatar"] = f"/api/avatars/{filename}"
            self._write(data)

        previous_name = previous_avatar.removeprefix("/api/avatars/").split("?", 1)[0]
        previous_path = avatar_dir / Path(previous_name).name
        if previous_name and previous_path != filepath and previous_path.parent == avatar_dir and previous_path.exists():
            previous_path.unlink(missing_ok=True)
        return self._public_user(user)

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
            user["last_login_at"] = self._now()
            self._write(data)
        return {"token": token, "user": self._public_user(user)}

    def authenticate(self, token: str) -> dict[str, Any]:
        token_hash = self._hash_token(token)
        with self._lock:
            for user in self._read()["users"].values():
                if any(hmac.compare_digest(item, token_hash) for item in user.get("sessions", [])):
                    return self._public_user(user)
        raise AuthError("登录状态已失效，请重新登录")

    def list_users(self) -> dict[str, Any]:
        with self._lock:
            users = [self._admin_user_summary(user) for user in self._read()["users"].values()]
        users.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return {
            "total": len(users),
            "onboarding_completed": sum(bool(item["onboarding_completed"]) for item in users),
            "active_users": sum(bool(item["active_sessions"]) for item in users),
            "users": users,
        }

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

    def _ensure_admin_user(self) -> None:
        if not self.admin_username or not self.admin_password:
            return
        self._validate_credentials(self.admin_username, self.admin_password)
        with self._lock:
            data = self._read()
            user = data["users"].get(self.admin_username)
            if user is None:
                salt = secrets.token_hex(16)
                user = {
                    "username": self.admin_username,
                    "display_name": self.admin_display_name,
                    "salt": salt,
                    "password_hash": "",
                    "created_at": self._now(),
                    "sessions": [],
                    "onboarding_completed": True,
                    "onboarding_profile": {},
                    "role": "admin",
                }
                data["users"][self.admin_username] = user
            user["display_name"] = self.admin_display_name
            user["role"] = "admin"
            user["password_hash"] = self._hash_password(self.admin_password, user["salt"])
            self._write(data)

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
            "role": user.get("role", "user"),
        }

    @classmethod
    def _admin_user_summary(cls, user: dict[str, Any]) -> dict[str, Any]:
        public = cls._public_user(user)
        public.update({
            "last_login_at": user.get("last_login_at"),
            "active_sessions": len(user.get("sessions", [])),
        })
        return public

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"users": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
