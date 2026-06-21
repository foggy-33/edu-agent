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


MAX_PDF_BYTES = 20 * 1024 * 1024


class ResourceError(ValueError):
    pass


class ResourceService:
    def __init__(self) -> None:
        self.base_dir = Path(get_settings().resource_data_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def upload_pdf(self, *, user_id: str, filename: str, stream: BinaryIO) -> dict[str, Any]:
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
                        raise ResourceError("PDF 文件不能超过 20 MB")
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
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            (resource_dir / "content.txt").write_text(text, encoding="utf-8")
            (resource_dir / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return metadata
        except Exception:
            shutil.rmtree(resource_dir, ignore_errors=True)
            raise

    def list_resources(self, user_id: str) -> list[dict[str, Any]]:
        resources: list[dict[str, Any]] = []
        for path in self.base_dir.glob("*/metadata.json"):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata.get("user_id") == user_id:
                resources.append(metadata)
        return sorted(resources, key=lambda item: item["created_at"], reverse=True)

    def get_metadata(self, user_id: str, file_id: str) -> dict[str, Any]:
        metadata_path = self._resource_dir(file_id) / "metadata.json"
        if not metadata_path.exists():
            raise ResourceError("资源不存在")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("user_id") != user_id:
            raise ResourceError("无权访问该资源")
        return metadata

    def get_pdf_path(self, user_id: str, file_id: str) -> Path:
        self.get_metadata(user_id, file_id)
        return self._resource_dir(file_id) / "source.pdf"

    def delete(self, user_id: str, file_id: str) -> None:
        self.get_metadata(user_id, file_id)
        with self._lock:
            shutil.rmtree(self._resource_dir(file_id))

    def build_context(self, user_id: str, file_ids: list[str], max_chars: int = 24000) -> tuple[str, list[dict[str, Any]]]:
        blocks: list[str] = []
        sources: list[dict[str, Any]] = []
        remaining = max_chars
        for file_id in dict.fromkeys(file_ids):
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
