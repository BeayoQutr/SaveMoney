import importlib
import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


def create_legacy_db(db_path: Path, sql_statements: list[str]) -> None:
    """Create a SQLite database from raw statements (no SQLAlchemy)."""
    conn = sqlite3.connect(db_path)
    try:
        for stmt in sql_statements:
            conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


class LegacyDbCompatTest(unittest.TestCase):
    """Test that the backend auto-migrates old SQLite databases on startup."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()
        os.environ.pop("SAVEMONEY_DATABASE_URL", None)

    def _bootstrap_app_with_legacy_db(self, db_name: str) -> tuple:
        """
        Point at a pre-created legacy SQLite file, then simulate the full
        startup path: create_all + ensure_sqlite_schema_compatibility.
        Returns (TestClient, SQLAlchemy engine).
        """
        db_path = Path(self.temp_dir.name) / db_name
        os.environ["SAVEMONEY_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

        # Import order: database -> models -> main (so Base.metadata has all tables)
        import app.database
        import app.models
        import app.main

        importlib.reload(app.database)
        importlib.reload(app.models)
        importlib.reload(app.main)

        from fastapi.testclient import TestClient
        from app.main import app
        from app.database import engine as app_engine

        client = TestClient(app)
        return client, app_engine

    def tearDown(self) -> None:
        import app.database

        app.database.engine.dispose()

    # ── 1. 只有基础 expenses 表的旧数据库 ──────────────────────────────
    def test_basic_expenses_table_gets_all_new_columns_and_backfill(self) -> None:
        db_path = Path(self.temp_dir.name) / "basic_expenses_only.db"
        create_legacy_db(
            db_path,
            [
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    note VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR NOT NULL,
                    created_at DATETIME
                )
                """,
                "INSERT INTO expenses (amount, note, date, category) VALUES (12.50, '午餐拉面', '2025-03-15', '餐饮')",
                "INSERT INTO expenses (amount, note, date, category) VALUES (3.00, '地铁', '2025-03-16', '交通')",
            ],
        )

        client, engine = self._bootstrap_app_with_legacy_db("basic_expenses_only.db")

        # Schema should have all new columns
        with engine.connect() as conn:
            from sqlalchemy import text

            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(expenses)")).fetchall()}
        self.assertIn("amount_cents", cols)
        self.assertIn("payment_method", cols)
        self.assertIn("is_necessary", cols)

        # Cents backfilled
        response = client.get("/expenses?limit=10")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["amount"], 3.0)   # sorted by date desc
        self.assertEqual(items[1]["amount"], 12.5)

        # Can create new expense with new fields
        create_resp = client.post(
            "/expenses",
            json={
                "amount": 25.0,
                "note": "买书",
                "date": "2025-03-17",
                "category": "学习",
                "payment_method": "微信",
                "is_necessary": 1,
            },
        )
        self.assertEqual(create_resp.status_code, 200)
        self.assertEqual(create_resp.json()["payment_method"], "微信")

        # Monthly summary still works
        summary = client.get("/expenses/summary/monthly?month=2025-03")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json()["count"], 3)
        self.assertEqual(summary.json()["total_amount"], 40.5)

    # ── 2. 缺少 amount_cents 字段的数据库 ──────────────────────────────
    def test_missing_amount_cents_column_backfills_and_works(self) -> None:
        db_path = Path(self.temp_dir.name) / "missing_amount_cents.db"
        create_legacy_db(
            db_path,
            [
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    note VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR NOT NULL,
                    payment_method TEXT,
                    is_necessary INTEGER,
                    created_at DATETIME
                )
                """,
                """
                INSERT INTO expenses (amount, note, date, category, payment_method, is_necessary)
                VALUES (45.67, '超市购物', '2025-04-01', '购物', '支付宝', 0)
                """,
            ],
        )

        client, engine = self._bootstrap_app_with_legacy_db("missing_amount_cents.db")

        # amount_cents column added
        with engine.connect() as conn:
            from sqlalchemy import text

            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(expenses)")).fetchall()}
        self.assertIn("amount_cents", cols)

        # Cents backfilled from legacy amount
        response = client.get("/expenses?limit=10")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["amount"], 45.67)

        # New expense still works
        create_resp = client.post(
            "/expenses",
            json={
                "amount": 8.88,
                "note": "早餐",
                "date": "2025-04-02",
                "category": "餐饮",
            },
        )
        self.assertEqual(create_resp.status_code, 200)
        self.assertEqual(create_resp.json()["amount"], 8.88)

    # ── 3. 缺少 payment_method / is_necessary 字段的数据库 ────────────
    def test_missing_payment_method_is_necessary_columns_added(self) -> None:
        db_path = Path(self.temp_dir.name) / "missing_payment_necessary.db"
        create_legacy_db(
            db_path,
            [
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    amount_cents INTEGER,
                    note VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR NOT NULL,
                    created_at DATETIME
                )
                """,
                """
                INSERT INTO expenses (amount, amount_cents, note, date, category)
                VALUES (99.99, 9999, '旧记录', '2025-02-14', '娱乐')
                """,
            ],
        )

        client, engine = self._bootstrap_app_with_legacy_db("missing_payment_necessary.db")

        with engine.connect() as conn:
            from sqlalchemy import text

            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(expenses)")).fetchall()}
        self.assertIn("payment_method", cols)
        self.assertIn("is_necessary", cols)

        # Old data preserved
        resp = client.get("/expenses?limit=10")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["items"][0]["note"], "旧记录")
        self.assertEqual(resp.json()["items"][0]["amount"], 99.99)

        # New record can include those fields
        create_resp = client.post(
            "/expenses",
            json={
                "amount": 5.5,
                "note": "公交",
                "date": "2025-02-15",
                "category": "交通",
                "payment_method": "公交卡",
                "is_necessary": 1,
            },
        )
        self.assertEqual(create_resp.status_code, 200)
        self.assertEqual(create_resp.json()["payment_method"], "公交卡")

    # ── 4. 没有 saving_plans 表的数据库 ─────────────────────────────────
    def test_no_saving_plans_table_does_not_crash(self) -> None:
        db_path = Path(self.temp_dir.name) / "no_plans_table.db"
        create_legacy_db(
            db_path,
            [
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    note VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR NOT NULL,
                    created_at DATETIME
                )
                """,
                "INSERT INTO expenses (amount, note, date, category) VALUES (10.0, '快餐', '2025-05-01', '餐饮')",
            ],
        )

        client, engine = self._bootstrap_app_with_legacy_db("no_plans_table.db")

        # App starts fine — Base.metadata.create_all creates saving_plans table
        with engine.connect() as conn:
            from sqlalchemy import text

            tables = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()
            }
        self.assertIn("saving_plans", tables)

        # Plans endpoints don't crash
        current = client.get("/plans/current")
        self.assertEqual(current.status_code, 200)
        self.assertIsNone(current.json()["plan"])

        # Generate a plan works
        gen_resp = client.post(
            "/plans/generate",
            json={
                "monthly_income": 4000,
                "fixed_expenses": 2000,
                "target_amount": 6000,
                "deadline": (date.today() + timedelta(days=90)).isoformat(),
                "identity": "worker",
                "minimum_living_cost": 1000,
            },
        )
        self.assertEqual(gen_resp.status_code, 200)

        # Expenses still work
        create_resp = client.post(
            "/expenses",
            json={
                "amount": 15.0,
                "note": "午餐",
                "date": "2025-05-02",
                "category": "餐饮",
            },
        )
        self.assertEqual(create_resp.status_code, 200)

        # Latest plan visible
        current2 = client.get("/plans/current")
        self.assertEqual(current2.status_code, 200)
        self.assertIsNotNone(current2.json()["plan"])

    # ── 5. 已有历史消费记录但没有整数分字段的数据库 ─────────────────
    def test_historical_data_without_cents_backfilled_correctly(self) -> None:
        db_path = Path(self.temp_dir.name) / "historical_no_cents.db"
        create_legacy_db(
            db_path,
            [
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    note VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR NOT NULL,
                    created_at DATETIME
                )
                """,
                "INSERT INTO expenses (amount, note, date, category) VALUES (0.5, '便宜货', '2025-01-05', '购物')",
                "INSERT INTO expenses (amount, note, date, category) VALUES (0.99, '小零食', '2025-01-05', '餐饮')",
                "INSERT INTO expenses (amount, note, date, category) VALUES (100.0, '大件', '2025-01-10', '购物')",
                "INSERT INTO expenses (amount, note, date, category) VALUES (12.345, '精确金额', '2025-01-15', '其他')",
                "INSERT INTO expenses (amount, note, date, category) VALUES (0.01, '一分钱', '2025-01-20', '其他')",
            ],
        )

        client, engine = self._bootstrap_app_with_legacy_db("historical_no_cents.db")

        # All 5 records preserved
        resp = client.get("/expenses?limit=20")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["items"]
        self.assertEqual(len(items), 5)

        # Monthly summary computes correctly
        summary = client.get("/expenses/summary/monthly?month=2025-01")
        self.assertEqual(summary.status_code, 200)
        data = summary.json()
        self.assertEqual(data["count"], 5)
        # Total: 0.5 + 0.99 + 100.0 + 12.35(rounded) + 0.01 = 113.85
        self.assertEqual(data["total_amount"], 113.85)

        # Category summary works
        cat_sum = client.get(
            "/expenses/summary/category?start_date=2025-01-01&end_date=2025-01-31"
        )
        self.assertEqual(cat_sum.status_code, 200)
        cat_items = {i["category"]: i for i in cat_sum.json()["items"]}
        self.assertEqual(cat_items["购物"]["count"], 2)
        self.assertEqual(cat_items["购物"]["total_amount"], 100.5)

        # New expense writes still work alongside old data
        create_resp = client.post(
            "/expenses",
            json={
                "amount": 7.77,
                "note": "新记录",
                "date": "2025-01-25",
                "category": "餐饮",
            },
        )
        self.assertEqual(create_resp.status_code, 200)

        resp2 = client.get("/expenses?limit=20")
        self.assertEqual(resp2.json()["total"], 6)

    # ── 6. 旧版 saving_plans 无 cents 字段但保留数据 ──────────────────
    def test_legacy_saving_plans_without_cents_preserves_all_data(self) -> None:
        db_path = Path(self.temp_dir.name) / "legacy_plans_no_cents.db"
        create_legacy_db(
            db_path,
            [
                """
                CREATE TABLE expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount FLOAT NOT NULL,
                    note VARCHAR NOT NULL,
                    date DATE NOT NULL,
                    category VARCHAR NOT NULL
                )
                """,
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
                    status TEXT DEFAULT 'active',
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """,
                """
                INSERT INTO saving_plans (
                    target_amount, deadline, monthly_income,
                    fixed_expenses, minimum_living_cost, saved_amount
                )
                VALUES (5000, '2025-12-31', 6000, 2500, 1200, 888.88)
                """,
            ],
        )

        client, engine = self._bootstrap_app_with_legacy_db("legacy_plans_no_cents.db")

        # Plan preserved
        current = client.get("/plans/current")
        self.assertEqual(current.status_code, 200)
        plan = current.json()["plan"]
        self.assertEqual(plan["target_amount"], 5000)
        self.assertEqual(plan["saved_amount"], 888.88)

        # Cents columns exist
        with engine.connect() as conn:
            from sqlalchemy import text

            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(saving_plans)")).fetchall()}
        for col in [
            "target_amount_cents",
            "monthly_income_cents",
            "fixed_expenses_cents",
            "minimum_living_cost_cents",
            "saved_amount_cents",
        ]:
            self.assertIn(col, cols, f"Expected {col} to be added")

        # Update saved amount works
        update_resp = client.put(
            f"/plans/{plan['id']}",
            json={"saved_amount": 999.99},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.json()["saved_amount"], 999.99)


if __name__ == "__main__":
    unittest.main()