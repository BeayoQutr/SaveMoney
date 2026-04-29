import os
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient


class SaveMoneyApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test.db"
        os.environ["SAVEMONEY_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

        from app.main import app

        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        from app.database import engine

        engine.dispose()
        cls.temp_dir.cleanup()
        os.environ.pop("SAVEMONEY_DATABASE_URL", None)

    def test_expense_crud_trims_note_and_normalizes_category(self) -> None:
        create_response = self.client.post(
            "/expenses",
            json={
                "amount": 12.5,
                "note": " 午餐 ",
                "date": "2026-04-29",
                "category": "餐饮",
            },
        )

        self.assertEqual(create_response.status_code, 200)
        created = create_response.json()
        self.assertEqual(created["note"], "午餐")
        self.assertEqual(created["category"], "餐饮")

        update_response = self.client.put(
            f"/expenses/{created['id']}",
            json={
                "amount": 3.2,
                "note": " 地铁 ",
                "date": "2026-04-29",
                "category": "不存在的分类",
            },
        )

        self.assertEqual(update_response.status_code, 200)
        updated = update_response.json()
        self.assertEqual(updated["note"], "地铁")
        self.assertEqual(updated["category"], "交通")

        summary_response = self.client.get(
            "/expenses/summary/daily?query_date=2026-04-29"
        )
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(summary_response.json()["total_amount"], 3.2)

        delete_response = self.client.delete(f"/expenses/{created['id']}")
        self.assertEqual(delete_response.status_code, 200)

        second_delete_response = self.client.delete(f"/expenses/{created['id']}")
        self.assertEqual(second_delete_response.status_code, 404)

    def test_date_ranges_must_be_ordered(self) -> None:
        category_response = self.client.get(
            "/expenses/summary/category?start_date=2026-04-30&end_date=2026-04-01"
        )
        self.assertEqual(category_response.status_code, 422)

        export_response = self.client.get(
            "/expenses/export/csv?start_date=2026-04-30&end_date=2026-04-01"
        )
        self.assertEqual(export_response.status_code, 422)

    def test_invalid_month_returns_422(self) -> None:
        response = self.client.get("/expenses/summary/monthly?month=2026-13")
        self.assertEqual(response.status_code, 422)

    def test_ai_json_parser_accepts_fenced_json(self) -> None:
        from app.main import parse_ai_json_object

        parsed = parse_ai_json_object(
            '```json\n{"category": "餐饮", "reason": "备注包含午餐"}\n```'
        )

        self.assertEqual(parsed["category"], "餐饮")
        self.assertEqual(parsed["reason"], "备注包含午餐")

    def test_ai_json_parser_rejects_non_json(self) -> None:
        from app.main import parse_ai_json_object

        with self.assertRaises(HTTPException):
            parse_ai_json_object("无法分类")


if __name__ == "__main__":
    unittest.main()
