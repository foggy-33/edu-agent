from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, BinaryIO
from uuid import uuid4

from pypdf import PdfReader

from app.core.config import get_settings
from app.rag.vector_store import get_vector_store


MAX_PDF_BYTES = 500 * 1024 * 1024
LEGACY_RESOURCE_FOLDER = "历史资料"
DEFAULT_CATEGORY = "未分类"
GENERATED_CATEGORY = "AI生成"


class ResourceError(ValueError):
    pass


class ResourceService:
    def __init__(self) -> None:
        self.base_dir = Path(get_settings().resource_data_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def upload_pdf(self, *, user_id: str, filename: str, stream: BinaryIO, course_folder: str) -> dict[str, Any]:
        folder = self._normalize_required_folder(course_folder)
        if not filename.lower().endswith(".pdf"):
            raise ResourceError("仅支持上传 PDF 文件")

        file_id = uuid4().hex
        resource_dir = self.base_dir / file_id
        resource_dir.mkdir(parents=True, exist_ok=False)
        pdf_path = resource_dir / "source.pdf"

        size = 0
        try:
            with pdf_path.open("wb") as target:
                while chunk := stream.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_PDF_BYTES:
                        raise ResourceError("PDF 文件不能超过 500 MB")
                    target.write(chunk)

            pages = self._extract_pages(pdf_path)
            text = "\n\n".join(f"[第 {item['page']} 页]\n{item['text']}" for item in pages if item["text"])
            if not text.strip():
                raise ResourceError("PDF 中没有可提取的文字，暂不支持纯扫描图片 PDF")

            metadata = {
                "id": file_id,
                "user_id": user_id,
                "name": Path(filename).name,
                "type": "pdf",
                "size": size,
                "page_count": len(pages),
                "text_length": len(text),
                "status": "ready",
                "course_folder": folder,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            (resource_dir / "content.txt").write_text(text, encoding="utf-8")
            (resource_dir / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # 向量化存储到向量库
            try:
                vector_store = get_vector_store()
                vector_store.add_user_pdf(file_id, filename, text)
            except Exception:
                # 向量存储失败不影响主流程
                pass

            return metadata
        except Exception:
            shutil.rmtree(resource_dir, ignore_errors=True)
            raise

    def list_resources(self, user_id: str) -> list[dict[str, Any]]:
        resources: list[dict[str, Any]] = []
        for path in self.base_dir.glob("*/metadata.json"):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata.get("user_id") == user_id:
                resources.append(self._normalize_metadata(metadata))
        return sorted(resources, key=lambda item: item["created_at"], reverse=True)

    def get_metadata(self, user_id: str, file_id: str) -> dict[str, Any]:
        metadata_path = self._resource_dir(file_id) / "metadata.json"
        if not metadata_path.exists():
            raise ResourceError("资源不存在")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("user_id") != user_id:
            raise ResourceError("无权访问该资源")
        return self._normalize_metadata(metadata)

    def get_pdf_path(self, user_id: str, file_id: str) -> Path:
        self.get_metadata(user_id, file_id)
        return self._resource_dir(file_id) / "source.pdf"

    def get_content_path(self, user_id: str, file_id: str) -> Path:
        self.get_metadata(user_id, file_id)
        return self._resource_dir(file_id) / "content.txt"

    def get_resource_content(self, user_id: str, file_id: str) -> str:
        path = self.get_content_path(user_id, file_id)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def delete(self, user_id: str, file_id: str) -> None:
        self.get_metadata(user_id, file_id)
        with self._lock:
            shutil.rmtree(self._resource_dir(file_id))

        # 从向量库中移除
        try:
            vector_store = get_vector_store()
            vector_store.remove_user_pdf(file_id)
        except Exception:
            pass

    def save_generated_resource(
        self,
        *,
        user_id: str,
        name: str,
        content: str,
        resource_type: str,
        course_folder: str,
        source_type: str = "generated",
    ) -> dict[str, Any]:
        folder = (course_folder or "").strip() or DEFAULT_CATEGORY
        resource_type = resource_type or "markdown"
        if resource_type in ("review", "exercises"):
            resource_type = "markdown"

        file_id = uuid4().hex
        resource_dir = self.base_dir / file_id
        resource_dir.mkdir(parents=True, exist_ok=False)

        content_path = resource_dir / "content.txt"
        content_path.write_text(content, encoding="utf-8")

        metadata = {
            "id": file_id,
            "user_id": user_id,
            "name": name.strip()[:120] or "未命名资料",
            "type": resource_type,
            "size": len(content.encode("utf-8")),
            "page_count": 0,
            "text_length": len(content),
            "status": "ready",
            "course_folder": folder[:60],
            "source_type": source_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (resource_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return self._normalize_metadata(metadata)

    def update_resource_folder(self, user_id: str, file_id: str, course_folder: str) -> dict[str, Any]:
        metadata = self.get_metadata(user_id, file_id)
        folder = (course_folder or "").strip() or DEFAULT_CATEGORY
        resource_dir = self._resource_dir(file_id)
        metadata_path = resource_dir / "metadata.json"
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        data["course_folder"] = folder[:60]
        metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return self._normalize_metadata(data)

    def list_categories(self, user_id: str) -> list[dict[str, Any]]:
        resources = self.list_resources(user_id)
        category_map: dict[str, int] = {}
        for item in resources:
            cat = item.get("course_folder") or DEFAULT_CATEGORY
            category_map[cat] = category_map.get(cat, 0) + 1
        return [
            {"name": name, "count": count}
            for name, count in sorted(category_map.items(), key=lambda x: x[0])
        ]

    def build_context(self, user_id: str, file_ids: list[str], max_chars: int = 24000) -> tuple[str, list[dict[str, Any]]]:
        return self.build_context_with_rag(user_id, file_ids)

    def build_context_with_rag(
        self,
        user_id: str,
        file_ids: list[str],
        query: str = "",
        max_chars: int = 2000,
    ) -> tuple[str, list[dict[str, Any]]]:
        """使用 RAG 检索构建上下文，只返回最相关的片段（仅引用用户上传的 PDF 文件）"""
        blocks: list[str] = []
        sources: list[dict[str, Any]] = []
        seen_file_ids: set[str] = set()

        pdf_file_ids: list[str] = []
        for fid in dict.fromkeys(file_ids):
            try:
                meta = self.get_metadata(user_id, fid)
                if meta.get("type") == "pdf" and meta.get("source_type") == "uploaded":
                    pdf_file_ids.append(fid)
            except Exception:
                pass

        if query and pdf_file_ids:
            vector_store = get_vector_store()
            results = vector_store.similarity_search(query, top_k=5, file_ids=pdf_file_ids)
            
            for result in results:
                source_name = result.get("source", "")
                file_id = result.get("metadata", {}).get("file_id", "")
                blocks.append(f"【文件：{source_name}】\n{result['content']}")
                if file_id and file_id not in seen_file_ids:
                    sources.append({
                        "id": file_id,
                        "name": source_name,
                        "title": result.get("title", ""),
                    })
                    seen_file_ids.add(file_id)
        elif pdf_file_ids:
            remaining = max_chars
            for file_id in pdf_file_ids:
                metadata = self.get_metadata(user_id, file_id)
                text = (self._resource_dir(file_id) / "content.txt").read_text(encoding="utf-8")
                excerpt = text[:remaining]
                if not excerpt:
                    continue
                blocks.append(f"【文件：{metadata['name']}】\n{excerpt}")
                sources.append({
                    "id": metadata["id"],
                    "name": metadata["name"],
                    "page_count": metadata["page_count"],
                    "course_folder": metadata["course_folder"],
                })
                remaining -= len(excerpt)
                if remaining <= 0:
                    break

        return "\n\n".join(blocks), sources

    @staticmethod
    def _extract_pages(pdf_path: Path) -> list[dict[str, Any]]:
        try:
            reader = PdfReader(str(pdf_path))
            return [
                {"page": index + 1, "text": (page.extract_text() or "").strip()}
                for index, page in enumerate(reader.pages)
            ]
        except Exception as exc:
            raise ResourceError(f"PDF 解析失败：{exc}") from exc

    def _resource_dir(self, file_id: str) -> Path:
        if not file_id.isalnum():
            raise ResourceError("资源 ID 不合法")
        return self.base_dir / file_id

    @staticmethod
    def _normalize_required_folder(value: str | None) -> str:
        folder = (value or "").strip()
        if not folder:
            raise ResourceError("请先选择课程文件夹")
        return folder[:60]

    @classmethod
    def _normalize_metadata(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        folder = (metadata.get("course_folder") or "").strip()
        metadata["course_folder"] = folder[:60] or LEGACY_RESOURCE_FOLDER
        metadata["source_type"] = metadata.get("source_type", "uploaded")
        resource_type = metadata.get("type", "pdf")
        if resource_type in ("review", "exercises"):
            resource_type = "markdown"
        metadata["type"] = resource_type
        return metadata
