from __future__ import annotations

import json
from typing import Any, Iterator

import httpx

def call_llm(
    prompt: str,
    *,
    api_key: str = "",
    base_url: str = "https://api.siliconflow.cn/v1",
    model: str = "Pro/deepseek-ai/DeepSeek-V3.2",
    active_provider: str = "siliconflow",
    spark_api_password: str = "",
    spark_base_url: str = "https://spark-api-open.xf-yun.com/x2",
    spark_model: str = "spark-x",
    system_prompt: str = "你是严谨的中文教育资源生成助手。",
) -> str:
    """Use the browser-provided OpenAI-compatible config, or return mock sentinel."""
    credential = spark_api_password if active_provider == "spark" else api_key
    if not credential.strip():
        return ""

    request_base_url = spark_base_url if active_provider == "spark" else base_url
    request_model = spark_model if active_provider == "spark" else model

    payload: dict[str, Any] = {
        "model": request_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 8000,
    }
    normalized_base_url = request_base_url.rstrip("/")
    url = normalized_base_url if normalized_base_url.endswith("/chat/completions") else f"{normalized_base_url}/chat/completions"
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {credential}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]).strip()
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"大模型调用失败: {exc}") from exc


def stream_llm(
    prompt: str,
    *,
    api_key: str = "",
    base_url: str = "https://api.siliconflow.cn/v1",
    model: str = "Pro/deepseek-ai/DeepSeek-V3.2",
    active_provider: str = "siliconflow",
    spark_api_password: str = "",
    spark_base_url: str = "https://spark-api-open.xf-yun.com/x2",
    spark_model: str = "spark-x",
    system_prompt: str = "你是严谨的中文教育资源生成助手。",
) -> Iterator[str]:
    """Stream OpenAI-compatible chat completion chunks."""
    credential = spark_api_password if active_provider == "spark" else api_key
    if not credential.strip():
        return

    request_base_url = spark_base_url if active_provider == "spark" else base_url
    request_model = spark_model if active_provider == "spark" else model

    payload: dict[str, Any] = {
        "model": request_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 8000,
        "stream": True,
    }
    normalized_base_url = request_base_url.rstrip("/")
    url = normalized_base_url if normalized_base_url.endswith("/chat/completions") else f"{normalized_base_url}/chat/completions"
    try:
        with httpx.Client(timeout=120.0) as client:
            with client.stream(
                "POST",
                url,
                headers={"Authorization": f"Bearer {credential}", "Content-Type": "application/json"},
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ").strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)["choices"][0].get("delta", {}).get("content", "")
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                        raise ValueError(f"大模型流式响应解析失败: {exc}") from exc
                    if chunk:
                        yield str(chunk)
    except httpx.HTTPError as exc:
        raise ValueError(f"大模型流式调用失败: {exc}") from exc
