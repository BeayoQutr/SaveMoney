import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient


class SaveMoneyApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test.db"
        cls.db_path = db_path
        os.environ["SAVEMONEY_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

        from app.main import app

        cls.client = TestClient(app)

    def setUp(self) -> None:
        from app.database import SessionLocal
        from app.models import Expense, SavingPlan

        db = SessionLocal()
        try:
            db.query(Expense).delete()
            db.query(SavingPlan).delete()
            db.commit()
        finally:
            db.close()

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

    def test_expense_summaries_and_csv_export(self) -> None:
        first = self.client.post(
            "/expenses",
            json={
                "amount": 10.1,
                "note": "午餐",
                "date": "2026-04-10",
                "category": "餐饮",
            },
        )
        second = self.client.post(
            "/expenses",
            json={
                "amount": 2.35,
                "note": "公交",
                "date": "2026-04-10",
                "category": "交通",
            },
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        daily = self.client.get("/expenses/summary/daily?query_date=2026-04-10")
        self.assertEqual(daily.status_code, 200)
        self.assertEqual(daily.json()["total_amount"], 12.45)
        self.assertEqual(daily.json()["count"], 2)

        category = self.client.get(
            "/expenses/summary/category?start_date=2026-04-01&end_date=2026-04-30"
        )
        self.assertEqual(category.status_code, 200)
        items = {item["category"]: item for item in category.json()["items"]}
        self.assertEqual(items["餐饮"]["total_amount"], 10.1)
        self.assertEqual(items["交通"]["total_amount"], 2.35)

        monthly = self.client.get("/expenses/summary/monthly?month=2026-04")
        self.assertEqual(monthly.status_code, 200)
        monthly_data = monthly.json()
        self.assertEqual(monthly_data["total_amount"], 12.45)
        self.assertEqual(monthly_data["count"], 2)
        self.assertEqual(monthly_data["average_daily_amount"], 0.42)
        self.assertEqual(
            [item["category"] for item in monthly_data["items"]],
            ["餐饮", "交通"],
        )

        csv_response = self.client.get(
            "/expenses/export/csv?start_date=2026-04-01&end_date=2026-04-30"
        )
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("text/csv", csv_response.headers["content-type"])
        self.assertIn(
            'attachment; filename="expenses_2026-04-01_to_2026-04-30.csv"',
            csv_response.headers["content-disposition"],
        )
        self.assertTrue(csv_response.text.startswith("\ufeffid,amount,note,date,category"))
        self.assertIn("10.10,午餐,2026-04-10,餐饮", csv_response.text)
        self.assertIn("午餐", csv_response.text)

    def test_expense_list_and_csv_prefer_cents_for_legacy_rows(self) -> None:
        from app.database import SessionLocal
        from app.models import Expense

        db = SessionLocal()
        try:
            db.add(
                Expense(
                    amount=12.345,
                    amount_cents=1235,
                    note="旧金额",
                    date=date(2026, 4, 10),
                    category="其他",
                )
            )
            db.commit()
        finally:
            db.close()

        list_response = self.client.get("/expenses?limit=10")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["items"][0]["amount"], 12.35)

        csv_response = self.client.get(
            "/expenses/export/csv?start_date=2026-04-01&end_date=2026-04-30"
        )
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("12.35,旧金额,2026-04-10,其他", csv_response.text)

    def test_monthly_summary_empty_month_returns_zero_state(self) -> None:
        monthly = self.client.get("/expenses/summary/monthly?month=2026-04")

        self.assertEqual(monthly.status_code, 200)
        self.assertEqual(
            monthly.json(),
            {
                "month": "2026-04",
                "total_amount": 0.0,
                "count": 0,
                "average_daily_amount": 0.0,
                "items": [],
            },
        )

    def test_date_ranges_must_be_ordered(self) -> None:
        list_response = self.client.get(
            "/expenses?start_date=2026-04-30&end_date=2026-04-01"
        )
        self.assertEqual(list_response.status_code, 422)

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

    def test_expense_list_pagination_is_bounded(self) -> None:
        negative_offset = self.client.get("/expenses?offset=-1")
        self.assertEqual(negative_offset.status_code, 422)

        excessive_limit = self.client.get("/expenses?limit=201")
        self.assertEqual(excessive_limit.status_code, 422)

    def test_expense_list_limit_offset_returns_requested_page(self) -> None:
        for amount, note, expense_date in [
            (1, "第一笔", "2026-04-01"),
            (2, "第二笔", "2026-04-02"),
            (3, "第三笔", "2026-04-03"),
        ]:
            response = self.client.post(
                "/expenses",
                json={
                    "amount": amount,
                    "note": note,
                    "date": expense_date,
                    "category": "其他",
                },
            )
            self.assertEqual(response.status_code, 200)

        page = self.client.get("/expenses?limit=1&offset=1")

        self.assertEqual(page.status_code, 200)
        data = page.json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["limit"], 1)
        self.assertEqual(data["offset"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["note"], "第二笔")

    def test_csv_import_creates_expenses_and_reports_bad_rows(self) -> None:
        csv_content = (
            "\ufeffamount,note,date,category\n"
            "12.50,午餐,2026-04-12,餐饮\n"
            "0,无效金额,2026-04-12,餐饮\n"
            "3.25,地铁,2026-04-13,交通\n"
        ).encode("utf-8")

        response = self.client.post(
            "/backup/import-csv",
            files={"file": ("expenses.csv", csv_content, "text/csv")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["imported"], 2)
        self.assertEqual(len(data["errors"]), 1)
        self.assertIn("第2行", data["errors"][0])
        self.assertTrue(Path(data["backup_path"]).exists())

        imported = self.client.get("/expenses?limit=10")
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(imported.json()["total"], 2)

    def test_backup_uses_configured_sqlite_database_path(self) -> None:
        from app.utils.backup_utils import get_db_path

        self.assertEqual(get_db_path(), self.db_path.resolve())

    def test_restore_db_replaces_configured_sqlite_database(self) -> None:
        from app.database import engine

        original_backup = Path(self.temp_dir.name) / "original_before_restore.db"
        restore_source = Path(self.temp_dir.name) / "restore_source.db"
        shutil.copy2(self.db_path, original_backup)
        shutil.copy2(self.db_path, restore_source)

        connection = sqlite3.connect(restore_source)
        try:
            connection.execute("CREATE TABLE restored_marker (value TEXT NOT NULL)")
            connection.execute("INSERT INTO restored_marker (value) VALUES ('ok')")
            connection.commit()
        finally:
            connection.close()

        try:
            with restore_source.open("rb") as restore_file:
                response = self.client.post(
                    "/backup/restore-db",
                    files={
                        "file": (
                            "restore_source.db",
                            restore_file,
                            "application/octet-stream",
                        )
                    },
                )

            self.assertEqual(response.status_code, 200)

            restored = sqlite3.connect(self.db_path)
            try:
                marker = restored.execute(
                    "SELECT value FROM restored_marker"
                ).fetchone()
            finally:
                restored.close()
            self.assertEqual(marker, ("ok",))
        finally:
            engine.dispose()
            shutil.copy2(original_backup, self.db_path)

    def test_saving_plan_money_fields_are_stored_as_cents(self) -> None:
        from app.database import SessionLocal
        from app.models import SavingPlan

        response = self.client.post(
            "/plans/generate",
            json={
                "monthly_income": 5000.12,
                "fixed_expenses": 1000.34,
                "target_amount": 1234.56,
                "deadline": (date.today() + timedelta(days=60)).isoformat(),
                "identity": "worker",
                "minimum_living_cost": 999.99,
            },
        )
        self.assertEqual(response.status_code, 200)

        db = SessionLocal()
        try:
            plan = db.query(SavingPlan).one()
            self.assertEqual(plan.target_amount_cents, 123456)
            self.assertEqual(plan.monthly_income_cents, 500012)
            self.assertEqual(plan.fixed_expenses_cents, 100034)
            self.assertEqual(plan.minimum_living_cost_cents, 99999)
            self.assertEqual(plan.saved_amount_cents, 0)

            update_response = self.client.put(
                f"/plans/{plan.id}",
                json={"saved_amount": 12.345},
            )
            self.assertEqual(update_response.status_code, 200)
            db.refresh(plan)
            self.assertEqual(plan.saved_amount_cents, 1235)
            self.assertEqual(update_response.json()["saved_amount"], 12.35)
        finally:
            db.close()

    def test_invalid_and_impossible_saving_plans_are_not_persisted(self) -> None:
        from app.database import SessionLocal
        from app.models import SavingPlan

        invalid_response = self.client.post(
            "/plans/generate",
            json={
                "monthly_income": 5000,
                "fixed_expenses": 1000,
                "target_amount": 1000,
                "deadline": (date.today() - timedelta(days=1)).isoformat(),
                "identity": "worker",
                "minimum_living_cost": 1000,
            },
        )
        impossible_response = self.client.post(
            "/plans/generate",
            json={
                "monthly_income": 1000,
                "fixed_expenses": 1000,
                "target_amount": 1000,
                "deadline": (date.today() + timedelta(days=10)).isoformat(),
                "identity": "worker",
                "minimum_living_cost": 1000,
            },
        )

        self.assertEqual(invalid_response.status_code, 200)
        self.assertEqual(invalid_response.json()["status"], "invalid")
        self.assertEqual(impossible_response.status_code, 200)
        self.assertEqual(impossible_response.json()["status"], "impossible")

        db = SessionLocal()
        try:
            self.assertEqual(db.query(SavingPlan).count(), 0)
        finally:
            db.close()

        current = self.client.get("/plans/current")
        self.assertEqual(current.status_code, 200)
        self.assertIsNone(current.json()["plan"])

    def test_current_saving_plan_returns_calculated_progress(self) -> None:
        deadline = date.today() + timedelta(days=10)
        create_response = self.client.post(
            "/plans/generate",
            json={
                "monthly_income": 5000,
                "fixed_expenses": 1000,
                "target_amount": 1000,
                "deadline": deadline.isoformat(),
                "identity": "worker",
                "minimum_living_cost": 1000,
            },
        )
        self.assertEqual(create_response.status_code, 200)

        current = self.client.get("/plans/current")

        self.assertEqual(current.status_code, 200)
        data = current.json()
        self.assertEqual(data["remaining_days"], 10)
        self.assertEqual(data["daily_saving"], 100)
        self.assertEqual(data["daily_available"], 100)
        self.assertEqual(data["plan"]["target_amount"], 1000)

    def test_error_response_uses_unified_shape(self) -> None:
        response = self.client.get("/expenses/summary/monthly?month=2026-13")

        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["error"]["code"], "HTTP_422")
        self.assertEqual(data["error"]["message"], "month 格式错误，应为 YYYY-MM")

    def test_404_422_and_500_errors_use_unified_shape(self) -> None:
        not_found = self.client.delete("/expenses/999")
        self.assertEqual(not_found.status_code, 404)
        self.assertEqual(not_found.json()["error"]["code"], "HTTP_404")
        self.assertEqual(not_found.json()["error"]["message"], "消费记录不存在")

        validation = self.client.post(
            "/expenses",
            json={"amount": 0, "note": "", "date": "bad-date"},
        )
        self.assertEqual(validation.status_code, 422)
        self.assertEqual(validation.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(validation.json()["error"]["message"], "请求参数校验失败")
        self.assertIsInstance(validation.json()["error"]["details"], list)

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        with patch(
            "app.services.expense_service.list_expenses",
            side_effect=RuntimeError("database unavailable"),
        ):
            server_error = client.get("/expenses")

        self.assertEqual(server_error.status_code, 500)
        self.assertEqual(
            server_error.json()["error"],
            {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "details": None,
            },
        )

    def test_ai_json_parser_accepts_fenced_json(self) -> None:
        from app.utils.ai_json import parse_ai_json_object

        parsed = parse_ai_json_object(
            '```json\n{"category": "餐饮", "reason": "备注包含午餐"}\n```'
        )

        self.assertEqual(parsed["category"], "餐饮")
        self.assertEqual(parsed["reason"], "备注包含午餐")

    def test_ai_json_parser_rejects_non_json(self) -> None:
        from app.utils.ai_json import parse_ai_json_object

        with self.assertRaises(HTTPException):
            parse_ai_json_object("无法分类")

    def test_ai_without_api_key_returns_graceful_fallback(self) -> None:
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}):
            response = self.client.post("/ai/optimize-note", json={"note": " 午餐 "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["optimized_note"], "午餐")

        create_response = self.client.post(
            "/expenses",
            json={
                "amount": 8.8,
                "note": "早餐",
                "date": "2026-04-11",
            },
        )
        self.assertEqual(create_response.status_code, 200)

    def test_ai_category_without_api_key_falls_back_to_local_rule(self) -> None:
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}):
            response = self.client.post(
                "/ai/suggest-category",
                json={"amount": 15, "note": "午餐"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["category"], "餐饮")
        self.assertIn("本地规则", data["reason"])

    def test_ai_category_runtime_error_falls_back_to_local_rule(self) -> None:
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}), patch(
            "app.services.ai_service.call_deepseek",
            side_effect=RuntimeError("network down"),
        ):
            response = self.client.post(
                "/ai/suggest-category",
                json={"amount": 6, "note": "地铁"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["category"], "交通")
        self.assertIn("本地规则", data["reason"])

    def test_ai_category_invalid_json_falls_back_to_local_rule(self) -> None:
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}), patch(
            "app.services.ai_service.call_deepseek",
            return_value="不是 JSON",
        ):
            response = self.client.post(
                "/ai/suggest-category",
                json={"amount": 6, "note": "地铁"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["category"], "交通")
        self.assertIn("本地规则", data["reason"])

    def test_token_auth_can_require_bearer_token(self) -> None:
        with patch.dict(os.environ, {"SAVEMONEY_ACCESS_TOKEN": "secret"}):
            unauthorized = self.client.get("/expenses")
            wrong = self.client.get(
                "/expenses",
                headers={"Authorization": "Bearer wrong"},
            )
            authorized = self.client.get(
                "/expenses",
                headers={"Authorization": "Bearer secret"},
            )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(unauthorized.json()["error"]["code"], "HTTP_401")
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(authorized.status_code, 200)

    def test_ai_monthly_advice_without_api_key_returns_friendly_message(self) -> None:
        create_response = self.client.post(
            "/expenses",
            json={
                "amount": 9.9,
                "note": "午餐",
                "date": "2026-04-11",
            },
        )
        self.assertEqual(create_response.status_code, 200)

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}):
            response = self.client.get("/ai/monthly-advice?month=2026-04")

        self.assertEqual(response.status_code, 200)
        self.assertIn("未配置 DeepSeek API Key", response.json()["advice"])

    def test_startup_migration_repairs_legacy_sqlite_expense_schema(self) -> None:
        from sqlalchemy import create_engine, text
        from app.db_migrations import ensure_sqlite_schema_compatibility

        db_path = Path(self.temp_dir.name) / "legacy_schema.db"
        connection = sqlite3.connect(db_path)
        try:
            connection.execute(
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    note VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR NOT NULL,
                    created_at DATETIME
                )
                """
            )
            connection.execute(
                """
                INSERT INTO expenses (amount, note, date, category)
                VALUES (12.345, '午餐', '2026-04-29', '餐饮')
                """
            )
            connection.commit()
        finally:
            connection.close()

        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        try:
            ensure_sqlite_schema_compatibility(engine)
            with engine.connect() as conn:
                rows = conn.execute(text("PRAGMA table_info(expenses)")).fetchall()
                columns = {row[1] for row in rows}
                cents = conn.execute(
                    text("SELECT amount_cents FROM expenses WHERE note = '午餐'")
                ).scalar_one()

            self.assertIn("amount_cents", columns)
            self.assertIn("payment_method", columns)
            self.assertIn("is_necessary", columns)
            self.assertEqual(cents, 1235)
        finally:
            engine.dispose()

    def test_startup_migration_backfills_legacy_saving_plan_cents(self) -> None:
        from sqlalchemy import create_engine, text
        from app.db_migrations import ensure_sqlite_schema_compatibility

        db_path = Path(self.temp_dir.name) / "legacy_plan_schema.db"
        connection = sqlite3.connect(db_path)
        try:
            connection.execute(
                """
                CREATE TABLE saving_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_amount FLOAT NOT NULL,
                    deadline DATE NOT NULL,
                    monthly_income FLOAT NOT NULL,
                    fixed_expenses FLOAT NOT NULL,
                    minimum_living_cost FLOAT NOT NULL,
                    identity VARCHAR,
                    saved_amount REAL NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
            connection.execute(
                """
                INSERT INTO saving_plans (
                    target_amount,
                    deadline,
                    monthly_income,
                    fixed_expenses,
                    minimum_living_cost,
                    saved_amount
                )
                VALUES (1234.56, '2026-06-01', 5000.12, 1000.34, 999.99, 12.345)
                """
            )
            connection.commit()
        finally:
            connection.close()

        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        try:
            ensure_sqlite_schema_compatibility(engine)
            with engine.connect() as conn:
                rows = conn.execute(text("PRAGMA table_info(saving_plans)")).fetchall()
                columns = {row[1] for row in rows}
                cents = conn.execute(
                    text(
                        """
                        SELECT
                            target_amount_cents,
                            monthly_income_cents,
                            fixed_expenses_cents,
                            minimum_living_cost_cents,
                            saved_amount_cents
                        FROM saving_plans
                        """
                    )
                ).one()

            self.assertIn("target_amount_cents", columns)
            self.assertIn("monthly_income_cents", columns)
            self.assertIn("fixed_expenses_cents", columns)
            self.assertIn("minimum_living_cost_cents", columns)
            self.assertIn("saved_amount_cents", columns)
            self.assertEqual(tuple(cents), (123456, 500012, 100034, 99999, 1235))
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
