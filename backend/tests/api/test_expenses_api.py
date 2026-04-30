def test_expense_crud_trims_note_and_normalizes_category(api_client) -> None:
    create_response = api_client.post(
        "/expenses",
        json={
            "amount": 12.5,
            "note": " 午餐 ",
            "date": "2026-04-29",
            "category": "餐饮",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["note"] == "午餐"
    assert created["category"] == "餐饮"

    update_response = api_client.put(
        f"/expenses/{created['id']}",
        json={
            "amount": 3.2,
            "note": " 地铁 ",
            "date": "2026-04-29",
            "category": "不存在的分类",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["note"] == "地铁"
    assert updated["category"] == "交通"

    summary_response = api_client.get("/expenses/summary/daily?query_date=2026-04-29")
    assert summary_response.status_code == 200
    assert summary_response.json()["total_amount"] == 3.2

    delete_response = api_client.delete(f"/expenses/{created['id']}")
    assert delete_response.status_code == 200

    second_delete_response = api_client.delete(f"/expenses/{created['id']}")
    assert second_delete_response.status_code == 404


def test_expense_summaries_and_csv_export(api_client) -> None:
    first = api_client.post(
        "/expenses",
        json={
            "amount": 10.1,
            "note": "午餐",
            "date": "2026-04-10",
            "category": "餐饮",
        },
    )
    second = api_client.post(
        "/expenses",
        json={
            "amount": 2.35,
            "note": "公交",
            "date": "2026-04-10",
            "category": "交通",
        },
    )
    assert first.status_code == 200
    assert second.status_code == 200

    daily = api_client.get("/expenses/summary/daily?query_date=2026-04-10")
    assert daily.status_code == 200
    assert daily.json()["total_amount"] == 12.45
    assert daily.json()["count"] == 2

    category = api_client.get(
        "/expenses/summary/category?start_date=2026-04-01&end_date=2026-04-30"
    )
    assert category.status_code == 200
    items = {item["category"]: item for item in category.json()["items"]}
    assert items["餐饮"]["total_amount"] == 10.1
    assert items["交通"]["total_amount"] == 2.35

    monthly = api_client.get("/expenses/summary/monthly?month=2026-04")
    assert monthly.status_code == 200
    monthly_data = monthly.json()
    assert monthly_data["total_amount"] == 12.45
    assert monthly_data["count"] == 2
    assert monthly_data["average_daily_amount"] == 0.42
    assert [item["category"] for item in monthly_data["items"]] == ["餐饮", "交通"]

    csv_response = api_client.get(
        "/expenses/export/csv?start_date=2026-04-01&end_date=2026-04-30"
    )
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert (
        'attachment; filename="expenses_2026-04-01_to_2026-04-30.csv"'
        in csv_response.headers["content-disposition"]
    )
    assert csv_response.text.startswith("\ufeffid,amount,note,date,category")
    assert "10.10,午餐,2026-04-10,餐饮" in csv_response.text
    assert "午餐" in csv_response.text


def test_monthly_summary_empty_month_returns_zero_state(api_client) -> None:
    monthly = api_client.get("/expenses/summary/monthly?month=2026-04")

    assert monthly.status_code == 200
    assert monthly.json() == {
        "month": "2026-04",
        "total_amount": 0.0,
        "count": 0,
        "average_daily_amount": 0.0,
        "items": [],
    }


def test_date_ranges_must_be_ordered(api_client) -> None:
    list_response = api_client.get(
        "/expenses?start_date=2026-04-30&end_date=2026-04-01"
    )
    assert list_response.status_code == 422

    category_response = api_client.get(
        "/expenses/summary/category?start_date=2026-04-30&end_date=2026-04-01"
    )
    assert category_response.status_code == 422

    export_response = api_client.get(
        "/expenses/export/csv?start_date=2026-04-30&end_date=2026-04-01"
    )
    assert export_response.status_code == 422


def test_invalid_month_returns_422(api_client) -> None:
    response = api_client.get("/expenses/summary/monthly?month=2026-13")
    assert response.status_code == 422


def test_expense_list_pagination_is_bounded(api_client) -> None:
    negative_offset = api_client.get("/expenses?offset=-1")
    assert negative_offset.status_code == 422

    excessive_limit = api_client.get("/expenses?limit=201")
    assert excessive_limit.status_code == 422


def test_expense_list_limit_offset_returns_requested_page(api_client) -> None:
    for amount, note, expense_date in [
        (1, "第一笔", "2026-04-01"),
        (2, "第二笔", "2026-04-02"),
        (3, "第三笔", "2026-04-03"),
    ]:
        response = api_client.post(
            "/expenses",
            json={
                "amount": amount,
                "note": note,
                "date": expense_date,
                "category": "其他",
            },
        )
        assert response.status_code == 200

    page = api_client.get("/expenses?limit=1&offset=1")

    assert page.status_code == 200
    data = page.json()
    assert data["total"] == 3
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["note"] == "第二笔"
