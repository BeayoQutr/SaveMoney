import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)


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
        print("[DeepSeek Debug] URL:", request_url)
        print("[DeepSeek Debug] model:", model)
        print("[DeepSeek Debug] status_code:", e.response.status_code)
        print(
            "[DeepSeek Debug] response_text:",
            e.response.text[:1000] if e.response.text else "(empty)",
        )
        raise RuntimeError("DeepSeek API 调用失败") from e
    except httpx.RequestError as e:
        print("[DeepSeek Debug] URL:", request_url)
        print("[DeepSeek Debug] model:", model)
        print("[DeepSeek Debug] exception_type:", type(e).__name__)
        print("[DeepSeek Debug] exception:", str(e))
        raise RuntimeError("DeepSeek API 调用失败") from e
    except (KeyError, IndexError) as e:
        print("[DeepSeek Debug] URL:", request_url)
        print("[DeepSeek Debug] model:", model)
        print("[DeepSeek Debug] response_status:", response.status_code)
        try:
            raw_text = response.text[:1000] if response.text else "(empty)"
        except Exception:
            raw_text = "(unavailable)"
        print("[DeepSeek Debug] response_text:", raw_text)
        print("[DeepSeek Debug] exception_type:", type(e).__name__)
        print("[DeepSeek Debug] exception:", str(e))
        raise RuntimeError("DeepSeek API 调用失败") from e
