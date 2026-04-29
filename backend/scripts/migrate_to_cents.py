"""
One-time migration script: add new columns to expenses table and populate amount_cents.

Run with:  python -m scripts.migrate_to_cents
"""
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, engine
from app.db_migrations import ensure_sqlite_schema_compatibility
from app.models import Expense
from app.utils.money import to_cents


def main():
    ensure_sqlite_schema_compatibility(engine)
    print("  SQLite schema compatibility columns are ready.")

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
