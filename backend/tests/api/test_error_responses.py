from unittest.mock import patch

from fastapi.testclient import TestClient


def test_error_response_uses_unified_shape(api_client) -> None:
    response = api_client.get("/expenses/summary/monthly?month=2026-13")

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "HTTP_422"
    assert data["error"]["message"] == "month 格式错误，应为 YYYY-MM"


def test_404_422_and_500_errors_use_unified_shape(api_client, app) -> None:
    not_found = api_client.delete("/expenses/999")
    assert not_found.status_code == 404
    assert not_found.json()["error"]["code"] == "HTTP_404"
    assert not_found.json()["error"]["message"] == "消费记录不存在"

    validation = api_client.post(
        "/expenses",
        json={"amount": 0, "note": "", "date": "bad-date"},
    )
    assert validation.status_code == 422
    assert validation.json()["error"]["code"] == "VALIDATION_ERROR"
    assert validation.json()["error"]["message"] == "请求参数校验失败"
    assert isinstance(validation.json()["error"]["details"], list)

    client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "app.services.expense_service.list_expenses",
        side_effect=RuntimeError("database unavailable"),
    ):
        server_error = client.get("/expenses")

    assert server_error.status_code == 500
    assert server_error.json()["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "服务器内部错误",
        "details": None,
    }
