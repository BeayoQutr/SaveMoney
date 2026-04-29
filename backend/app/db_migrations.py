from sqlalchemy import Engine, text


SQLITE_COMPAT_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "expenses": [
        ("amount_cents", "INTEGER"),
        ("payment_method", "TEXT"),
        ("is_necessary", "INTEGER"),
    ],
    "saving_plans": [
        ("saved_amount", "REAL NOT NULL DEFAULT 0"),
        ("target_amount_cents", "INTEGER"),
        ("monthly_income_cents", "INTEGER"),
        ("fixed_expenses_cents", "INTEGER"),
        ("minimum_living_cost_cents", "INTEGER"),
        ("saved_amount_cents", "INTEGER"),
        ("status", "TEXT NOT NULL DEFAULT 'active'"),
        ("updated_at", "DATETIME"),
    ],
}


def ensure_sqlite_schema_compatibility(engine: Engine) -> None:
    """Add columns introduced after the initial SQLite schema was created."""
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as conn:
        for table_name, columns in SQLITE_COMPAT_COLUMNS.items():
            table_info = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            if not table_info:
                continue

            existing_columns = {row[1] for row in table_info}
            for column_name, column_type in columns:
                if column_name not in existing_columns:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )

        expense_columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info(expenses)")).fetchall()
        }
        if {"amount", "amount_cents"}.issubset(expense_columns):
            conn.execute(
                text(
                    """
                    UPDATE expenses
                    SET amount_cents = CAST(ROUND(amount * 100) AS INTEGER)
                    WHERE amount_cents IS NULL AND amount IS NOT NULL
                    """
                )
            )

        plan_columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info(saving_plans)")).fetchall()
        }
        plan_cent_columns = {
            "target_amount": "target_amount_cents",
            "monthly_income": "monthly_income_cents",
            "fixed_expenses": "fixed_expenses_cents",
            "minimum_living_cost": "minimum_living_cost_cents",
            "saved_amount": "saved_amount_cents",
        }
        for yuan_column, cents_column in plan_cent_columns.items():
            if {yuan_column, cents_column}.issubset(plan_columns):
                conn.execute(
                    text(
                        f"""
                        UPDATE saving_plans
                        SET {cents_column} = CAST(ROUND({yuan_column} * 100) AS INTEGER)
                        WHERE {cents_column} IS NULL AND {yuan_column} IS NOT NULL
                        """
                    )
                )
