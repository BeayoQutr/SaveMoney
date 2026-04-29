import os
import logging
from pathlib import Path

import httpx
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


def call_deepseek(
    messages: list[dict],
    temperature: float = 0.4,
    max_tokens: int = 500,
) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY")

    request_url = f"{base_url.rstrip('/')}/chat/completions"

    try:
        response = httpx.post(
            request_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            },
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.warning(
            "DeepSeek HTTP error status=%s model=%s",
            e.response.status_code,
            model,
        )
        raise RuntimeError("DeepSeek API 调用失败") from e
    except httpx.RequestError as e:
        logger.warning("DeepSeek request error type=%s model=%s", type(e).__name__, model)
        raise RuntimeError("DeepSeek API 调用失败") from e
    except (KeyError, IndexError) as e:
        logger.warning("DeepSeek response shape error type=%s model=%s", type(e).__name__, model)
        raise RuntimeError("DeepSeek API 调用失败") from e
