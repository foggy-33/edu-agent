from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class CourseMaterialError(ValueError):
    pass


class CourseMaterialService:
    def __init__(self) -> None:
        settings = get_settings()
        self.source_root = Path(settings.course_source_dir).resolve()
        self.annotation_root = Path(settings.course_annotation_dir).resolve()
        self.annotation_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(value: str) -> str:
        compact = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", value.strip())
        return compact[:80] or "unknown"

    def _course_folder(self, course: str) -> Path | None:
        course = course.strip()
        candidates = [course]
        if "数据库" in course:
            candidates.insert(0, "数据库")
        for name in candidates:
            folder = (self.source_root / name).resolve()
            if folder.parent == self.source_root and folder.is_dir():
                return folder
        return None

    @staticmethod
    def _material_id(path: Path) -> str:
        return hashlib.sha1(path.name.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _chapter_metadata(path: Path) -> tuple[int | None, int | None]:
        """Extract textbook chapter and optional volume numbers from courseware names."""
        chapter_match = re.search(r"第\s*(\d+)\s*章", path.stem, re.IGNORECASE)
        part_match = re.search(r"[（(]\s*(\d+)\s*[）)]", path.stem)
        chapter = int(chapter_match.group(1)) if chapter_match else None
        part = int(part_match.group(1)) if part_match else None
        return chapter, part

    def list_materials(self, course: str) -> list[dict[str, Any]]:
        folder = self._course_folder(course)
        if folder is None:
            return []
        pdfs = sorted(
            (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"),
            key=lambda path: [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)],
        )
        materials: list[dict[str, Any]] = []
        for path in pdfs:
            chapter, part = self._chapter_metadata(path)
            materials.append({
                "id": self._material_id(path),
                "name": path.stem,
                "filename": path.name,
                "size": path.stat().st_size,
                "chapter": chapter,
                "part": part,
            })
        return materials

    def material_path(self, course: str, material_id: str) -> Path:
        folder = self._course_folder(course)
        if folder is None:
            raise CourseMaterialError("该课程暂无内置 PDF 资料")
        for path in folder.iterdir():
            if path.is_file() and path.suffix.lower() == ".pdf" and self._material_id(path) == material_id:
                resolved = path.resolve()
                if resolved.parent != folder:
                    break
                return resolved
        raise CourseMaterialError("PDF 资料不存在")

    def _annotation_file(self, user_id: str, course: str, material_id: str) -> Path:
        user_dir = self.annotation_root / self._safe_name(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        course_key = hashlib.sha1(course.strip().encode("utf-8")).hexdigest()[:12]
        return user_dir / f"{course_key}-{self._safe_name(material_id)}.json"

    def list_annotations(self, user_id: str, course: str, material_id: str) -> list[dict[str, Any]]:
        self.material_path(course, material_id)
        path = self._annotation_file(user_id, course, material_id)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def add_annotation(
        self,
        *,
        user_id: str,
        course: str,
        material_id: str,
        page: int,
        content: str,
        x: float | None,
        y: float | None,
    ) -> dict[str, Any]:
        if page < 1:
            raise CourseMaterialError("批注页码无效")
        content = content.strip()
        if not content:
            raise CourseMaterialError("批注内容不能为空")
        if len(content) > 2000:
            raise CourseMaterialError("批注内容不能超过 2000 字")
        annotations = self.list_annotations(user_id, course, material_id)
        annotation = {
            "id": uuid.uuid4().hex,
            "page": page,
            "content": content,
            "x": max(0.0, min(1.0, x)) if x is not None else None,
            "y": max(0.0, min(1.0, y)) if y is not None else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        annotations.append(annotation)
        self._annotation_file(user_id, course, material_id).write_text(
            json.dumps(annotations, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return annotation

    def delete_annotation(self, user_id: str, course: str, material_id: str, annotation_id: str) -> None:
        annotations = self.list_annotations(user_id, course, material_id)
        filtered = [item for item in annotations if item.get("id") != annotation_id]
        if len(filtered) == len(annotations):
            raise CourseMaterialError("批注不存在")
        self._annotation_file(user_id, course, material_id).write_text(
            json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8"
        )
