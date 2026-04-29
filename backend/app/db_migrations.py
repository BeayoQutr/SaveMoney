from sqlalchemy import Engine, text


SQLITE_COMPAT_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "expenses": [
        ("amount_cents", "INTEGER"),
        ("payment_method", "TEXT"),
        ("is_necessary", "INTEGER"),
    ],
    "saving_plans": [
        ("saved_amount", "REAL NOT NULL DEFAULT 0"),
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
