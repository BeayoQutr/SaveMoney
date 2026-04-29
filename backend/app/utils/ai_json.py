import json
from collections.abc import Mapping

from fastapi import HTTPException


def parse_ai_json_object(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试") from None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试") from None

    if not isinstance(data, Mapping):
        raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后再试")
    return dict(data)
