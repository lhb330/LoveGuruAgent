from typing import Any

from common.constants import DEFAULT_SUCCESS_MSG, SUCCESS_CODE


def success(data: Any = None, msg: str = DEFAULT_SUCCESS_MSG) -> dict[str, Any]:
    return {"code": SUCCESS_CODE, "msg": msg, "data": data}


def fail(msg: str, code: int = 1, data: Any = None) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}
