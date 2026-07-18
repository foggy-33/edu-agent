from __future__ import annotations

from typing import Any


def resolve_spark_config(
    settings: Any,
    *,
    api_password: str = "",
    base_url: str = "",
    model: str = "",
) -> tuple[str, str, str]:
    """Resolve a public model choice to credentials kept only on the server."""
    requested_model = (model or settings.spark_model).strip()
    if requested_model in {"lite", "spark-lite"}:
        return (
            api_password or settings.spark_lite_api_password,
            base_url or settings.spark_lite_base_url,
            settings.spark_lite_model,
        )
    return (
        api_password or settings.spark_api_password,
        base_url or settings.spark_base_url,
        requested_model or settings.spark_model,
    )
