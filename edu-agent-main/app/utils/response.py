from typing import Any


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def fail(message: str, data: Any = None) -> dict[str, Any]:
    return {"success": False, "message": message, "data": data}
