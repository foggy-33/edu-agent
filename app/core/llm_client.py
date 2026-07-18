from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import get_settings


class LLMClient:
    """LLM adapter. Mock mode is the default for local demos and tests."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.mode = self.settings.llm_mode.lower()

    def generate(self, prompt: str, task: str = "general", **kwargs: Any) -> str:
        if self.mode == "siliconflow":
            return self.siliconflow_generate(prompt=prompt, task=task, **kwargs)
        if self.mode == "mock":
            return self.mock_generate(prompt=prompt, task=task, **kwargs)
        if self.mode == "spark":
            return self.spark_generate(prompt=prompt, task=task, **kwargs)
        return self.mock_generate(prompt=prompt, task=task, **kwargs)

    def mock_generate(self, prompt: str, task: str = "general", **kwargs: Any) -> str:
        mock_outputs = {
            "document": (
                "# 个性化课程讲解文档\n\n"
                "## 学习目标\n"
                "围绕函数依赖、候选码与范式判断建立可操作的解题流程。\n\n"
                "## 核心方法\n"
                "1. 先列出关系模式和函数依赖集合。\n"
                "2. 通过属性闭包判断候选码。\n"
                "3. 根据主属性、非主属性和依赖类型判断 2NF、3NF、BCNF。\n\n"
                "## 例题\n"
                "设 R(A,B,C)，F={A->B, B->C}。A+={A,B,C}，因此 A 是候选码。\n"
                "由于 B->C 的左部 B 不是超码，R 不满足 BCNF。\n"
            ),
            "mindmap": (
                "mindmap\n"
                "  root((数据库系统复习))\n"
                "    函数依赖\n"
                "      属性闭包\n"
                "      最小依赖集\n"
                "    候选码\n"
                "      超码\n"
                "      主属性\n"
                "    范式判断\n"
                "      2NF\n"
                "      3NF\n"
                "      BCNF\n"
                "    SQL实操\n"
                "      建表\n"
                "      查询\n"
            ),
            "general": "这是 mock LLM 返回的结构化教学内容。",
        }
        return mock_outputs.get(task, mock_outputs["general"])

    def spark_generate(
        self,
        prompt: str,
        task: str = "general",
        *,
        spark_api_password: str = "",
        spark_base_url: str = "",
        spark_model: str = "",
        system_prompt: str = "你是一个严谨的智能学习助手。",
        temperature: float = 0.3,
        max_tokens: int = 1800,
        messages: list[dict[str, str]] | None = None,
        **_: Any,
    ) -> str:
        password = spark_api_password or self.settings.spark_api_password
        if not password:
            raise ValueError("未配置讯飞星火 API Password")

        base_url = (spark_base_url or self.settings.spark_base_url).rstrip("/")
        url = base_url if base_url.endswith("/chat/completions") else f"{base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": spark_model or self.settings.spark_model,
            "messages": messages or [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    url,
                    headers={"Authorization": f"Bearer {password}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise ValueError(f"讯飞星火请求失败 ({exc.response.status_code}): {detail}") from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"无法连接讯飞星火 API: {exc}") from exc

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"讯飞星火返回格式异常: {json.dumps(data, ensure_ascii=False)[:500]}") from exc

    def configured_generate(
        self,
        prompt: str,
        *,
        active_provider: str = "siliconflow",
        **kwargs: Any,
    ) -> str:
        if active_provider == "spark":
            return self.spark_generate(prompt, **kwargs)
        return self.siliconflow_generate(prompt, **kwargs)

    def siliconflow_generate(
        self,
        prompt: str,
        task: str = "general",
        *,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        system_prompt: str = "你是一个严谨的智能学习助手。",
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1800,
        messages: list[dict[str, str]] | None = None,
        **_: Any,
    ) -> str:
        key = api_key or self.settings.siliconflow_api_key
        if not key:
            raise ValueError("未配置硅基流动 API Key")

        url = f"{(base_url or self.settings.siliconflow_base_url).rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": model or self.settings.siliconflow_model,
            "messages": messages or [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise ValueError(f"硅基流动请求失败 ({exc.response.status_code}): {detail}") from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"无法连接硅基流动 API: {exc}") from exc

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"硅基流动返回格式异常: {json.dumps(data, ensure_ascii=False)[:500]}") from exc
