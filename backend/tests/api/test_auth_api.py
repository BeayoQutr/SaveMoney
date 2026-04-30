from unittest.mock import patch


def test_token_auth_can_require_bearer_token(api_client) -> None:
    with patch.dict("os.environ", {"SAVEMONEY_ACCESS_TOKEN": "secret"}):
        unauthorized = api_client.get("/expenses")
        wrong = api_client.get(
            "/expenses",
            headers={"Authorization": "Bearer wrong"},
        )
        authorized = api_client.get(
            "/expenses",
            headers={"Authorization": "Bearer secret"},
        )

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "HTTP_401"
    assert wrong.status_code == 401
    assert authorized.status_code == 200
