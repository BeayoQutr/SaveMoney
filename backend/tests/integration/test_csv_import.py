from pathlib import Path


def test_csv_import_creates_expenses_and_reports_bad_rows(api_client) -> None:
    csv_content = (
        "\ufeffamount,note,date,category\n"
        "12.50,午餐,2026-04-12,餐饮\n"
        "0,无效金额,2026-04-12,餐饮\n"
        "3.25,地铁,2026-04-13,交通\n"
    ).encode("utf-8")

    response = api_client.post(
        "/backup/import-csv",
        files={"file": ("expenses.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert len(data["errors"]) == 1
    assert "第2行" in data["errors"][0]
    assert Path(data["backup_path"]).exists()

    imported = api_client.get("/expenses?limit=10")
    assert imported.status_code == 200
    assert imported.json()["total"] == 2
