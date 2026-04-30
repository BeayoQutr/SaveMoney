from unittest.mock import patch


def test_ai_category_runtime_error_falls_back_to_local_rule(api_client) -> None:
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}), patch(
        "app.services.ai_service.call_deepseek",
        side_effect=RuntimeError("network down"),
    ):
        response = api_client.post(
            "/ai/suggest-category",
            json={"amount": 6, "note": "地铁"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "交通"
    assert "本地规则" in data["reason"]


def test_ai_category_invalid_json_falls_back_to_local_rule(api_client) -> None:
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}), patch(
        "app.services.ai_service.call_deepseek",
        return_value="不是 JSON",
    ):
        response = api_client.post(
            "/ai/suggest-category",
            json={"amount": 6, "note": "地铁"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "交通"
    assert "本地规则" in data["reason"]
