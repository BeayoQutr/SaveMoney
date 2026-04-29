"""
One-time migration script: add new columns to expenses table and populate amount_cents.

Run with:  python -m scripts.migrate_to_cents
"""
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, engine
from sqlalchemy import text
from app.models import Expense
from app.utils.money import to_cents


def column_exists(table: str, column: str) -> bool:
    """Check if a column exists in a SQLite table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        columns = [row[1] for row in result]
        return column in columns


def main():
    # Add new columns if they don't exist
    columns_to_add = [
        ("amount_cents", "INTEGER"),
        ("payment_method", "TEXT"),
        ("is_necessary", "INTEGER"),
    ]
    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            if not column_exists("expenses", col_name):
                conn.execute(text(f"ALTER TABLE expenses ADD COLUMN {col_name} {col_type}"))
                print(f"  Added column: {col_name} ({col_type})")
            else:
                print(f"  Column already exists: {col_name}")
        conn.commit()

    # Migrate amount -> amount_cents for records that don't have amount_cents yet
    db = SessionLocal()
    try:
        rows = db.query(Expense).filter(Expense.amount_cents.is_(None)).all()
        if not rows:
            print("  All records already have amount_cents. No migration needed.")
            return

        print(f"  Migrating {len(rows)} records...")
        errors = 0
        for row in rows:
            old_amount = row.amount
            new_cents = to_cents(old_amount)
            # Verify: the difference should be < 0.01 yuan
            reconstructed = new_cents / 100.0
            if abs(reconstructed - old_amount) >= 0.01:
                errors += 1
                print(f"    WARNING id={row.id}: amount={old_amount}, cents={new_cents}, diff={abs(reconstructed - old_amount)}")
            row.amount_cents = new_cents

        db.commit()
        print(f"  Migration complete. {len(rows)} records updated, {errors} warnings.")

        # Verify
        remaining = db.query(Expense).filter(Expense.amount_cents.is_(None)).count()
        print(f"  Remaining records without amount_cents: {remaining}")
    finally:
        db.close()


if __name__ == "__main__":
    main()