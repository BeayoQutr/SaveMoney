from unittest.mock import patch


def test_ai_without_api_key_returns_graceful_fallback(api_client) -> None:
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}):
        response = api_client.post("/ai/optimize-note", json={"note": " 午餐 "})

    assert response.status_code == 200
    assert response.json()["optimized_note"] == "午餐"

    create_response = api_client.post(
        "/expenses",
        json={
            "amount": 8.8,
            "note": "早餐",
            "date": "2026-04-11",
        },
    )
    assert create_response.status_code == 200


def test_ai_category_without_api_key_falls_back_to_local_rule(api_client) -> None:
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}):
        response = api_client.post(
            "/ai/suggest-category",
            json={"amount": 15, "note": "午餐"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "餐饮"
    assert "本地规则" in data["reason"]


def test_ai_monthly_advice_without_api_key_returns_friendly_message(api_client) -> None:
    create_response = api_client.post(
        "/expenses",
        json={
            "amount": 9.9,
            "note": "午餐",
            "date": "2026-04-11",
        },
    )
    assert create_response.status_code == 200

    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": ""}):
        response = api_client.get("/ai/monthly-advice?month=2026-04")

    assert response.status_code == 200
    assert "未配置 DeepSeek API Key" in response.json()["advice"]
