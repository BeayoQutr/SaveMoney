import sqlite3


def test_startup_migration_repairs_legacy_sqlite_expense_schema(tmp_path) -> None:
    from sqlalchemy import create_engine, text

    from app.db_migrations import ensure_sqlite_schema_compatibility

    db_path = tmp_path / "legacy_schema.db"
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

        assert "amount_cents" in columns
        assert "payment_method" in columns
        assert "is_necessary" in columns
        assert cents == 1235
    finally:
        engine.dispose()


def test_startup_migration_backfills_legacy_saving_plan_cents(tmp_path) -> None:
    from sqlalchemy import create_engine, text

    from app.db_migrations import ensure_sqlite_schema_compatibility

    db_path = tmp_path / "legacy_plan_schema.db"
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

        assert "target_amount_cents" in columns
        assert "monthly_income_cents" in columns
        assert "fixed_expenses_cents" in columns
        assert "minimum_living_cost_cents" in columns
        assert "saved_amount_cents" in columns
        assert tuple(cents) == (123456, 500012, 100034, 99999, 1235)
    finally:
        engine.dispose()
