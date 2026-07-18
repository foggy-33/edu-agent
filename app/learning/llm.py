from __future__ import annotations

import json
from typing import Any, Iterator

import httpx

from app.core.config import get_settings
from app.core.spark_config import resolve_spark_config

def call_llm(
    prompt: str,
    *,
    api_key: str = "",
    base_url: str = "https://api.siliconflow.cn/v1",
    model: str = "Pro/deepseek-ai/DeepSeek-V3.2",
    active_provider: str = "siliconflow",
    spark_api_password: str = "",
    spark_base_url: str = "",
    spark_model: str = "",
    system_prompt: str = "你是严谨的中文教育资源生成助手。",
) -> str:
    """Use the browser-provided OpenAI-compatible config, or return mock sentinel."""
    settings = get_settings()
    if active_provider == "spark":
        credential, request_base_url, request_model = resolve_spark_config(
            settings,
            api_password=spark_api_password,
            base_url=spark_base_url,
            model=spark_model,
        )
    else:
        credential = api_key or settings.siliconflow_api_key
        request_base_url = base_url or settings.siliconflow_base_url
        request_model = model or settings.siliconflow_model
    if not credential.strip():
        provider_name = "讯飞星火" if active_provider == "spark" else "硅基流动"
        raise ValueError(f"{provider_name}未配置 API 密钥，请检查服务器 .env 并重建后端容器")

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
        content = str(response.json()["choices"][0]["message"]["content"]).strip()
        if not content:
            raise ValueError("大模型返回内容为空")
        return content
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
    spark_base_url: str = "",
    spark_model: str = "",
    response_speed: str = "balanced",
    system_prompt: str = "你是严谨的中文教育资源生成助手。",
) -> Iterator[dict[str, str]]:
    """Stream normalized reasoning/content events from OpenAI-compatible APIs."""
    settings = get_settings()
    if active_provider == "spark":
        credential, request_base_url, request_model = resolve_spark_config(
            settings,
            api_password=spark_api_password,
            base_url=spark_base_url,
            model=spark_model,
        )
    else:
        credential = api_key or settings.siliconflow_api_key
        request_base_url = base_url or settings.siliconflow_base_url
        request_model = model or settings.siliconflow_model
    if not credential.strip():
        provider_name = "讯飞星火" if active_provider == "spark" else "硅基流动"
        raise ValueError(f"{provider_name}未配置 API 密钥，请检查服务器 .env 并重建后端容器")

    speed_options = {
        "fast": {
            "temperature": 0.2,
            "max_tokens": 4000,
            "instruction": "优先快速响应，直接给出关键结论，避免不必要的展开。",
        },
        "balanced": {
            "temperature": 0.35,
            "max_tokens": 8000,
            "instruction": "兼顾响应速度与内容完整性，给出必要分析和清晰结论。",
        },
        "deep": {
            "temperature": 0.3,
            "max_tokens": 12000,
            "instruction": "进行更充分的分析与核对，再给出完整、严谨的回答。",
        },
    }
    speed = speed_options.get(response_speed, speed_options["balanced"])
    payload: dict[str, Any] = {
        "model": request_model,
        "messages": [
            {"role": "system", "content": f"{system_prompt}\n{speed['instruction']}"},
            {"role": "user", "content": prompt},
        ],
        "temperature": speed["temperature"],
        "max_tokens": speed["max_tokens"],
        "stream": True,
    }
    normalized_base_url = request_base_url.rstrip("/")
    url = normalized_base_url if normalized_base_url.endswith("/chat/completions") else f"{normalized_base_url}/chat/completions"
    try:
        timeout = httpx.Timeout(connect=15.0, read=300.0, write=30.0, pool=30.0)
        with httpx.Client(timeout=timeout) as client:
            with client.stream(
                "POST",
                url,
                headers={
                    "Authorization": f"Bearer {credential}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "text/event-stream" not in content_type:
                    response.read()
                    try:
                        data = response.json()
                    except (json.JSONDecodeError, ValueError) as exc:
                        raise ValueError(f"大模型返回了无法解析的非流式响应: {response.text[:300]}") from exc
                    try:
                        message = data["choices"][0]["message"]
                    except (KeyError, IndexError, TypeError) as exc:
                        error = data.get("error") if isinstance(data, dict) else None
                        error_detail = error.get("message") if isinstance(error, dict) else error
                        error_message = (data.get("message") if isinstance(data, dict) else None) or error_detail or str(data)[:300]
                        raise ValueError(f"大模型调用失败: {error_message}") from exc
                    reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
                    content = message.get("content") or ""
                    if reasoning:
                        yield {"type": "reasoning", "text": str(reasoning)}
                    if content:
                        yield {"type": "content", "text": str(content)}
                        return
                    raise ValueError("大模型返回内容为空")

                received_content = False
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0].get("delta", {})
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                        raise ValueError(f"大模型流式响应解析失败: {exc}") from exc
                    reasoning = delta.get("reasoning_content") or delta.get("reasoning") or delta.get("thinking") or ""
                    content = delta.get("content") or ""
                    if isinstance(reasoning, list):
                        reasoning = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in reasoning)
                    if isinstance(content, list):
                        content = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
                    if reasoning:
                        yield {"type": "reasoning", "text": str(reasoning)}
                    if content:
                        received_content = True
                        yield {"type": "content", "text": str(content)}
                if not received_content:
                    raise ValueError("大模型连接成功，但没有返回可展示的回答内容")
    except httpx.HTTPError as exc:
        raise ValueError(f"大模型流式调用失败: {exc}") from exc
