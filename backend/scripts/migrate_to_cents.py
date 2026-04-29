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
from app.models import Expense, SavingPlan
from app.utils.money import to_cents


def main():
    ensure_sqlite_schema_compatibility(engine)
    print("  SQLite schema compatibility columns are ready.")

    db = SessionLocal()
    try:
        rows = db.query(Expense).filter(Expense.amount_cents.is_(None)).all()
        print(f"  Migrating {len(rows)} expense records...")
        for row in rows:
            row.amount_cents = to_cents(row.amount)

        plans = db.query(SavingPlan).all()
        migrated_plan_fields = 0
        for plan in plans:
            for yuan_attr, cents_attr in [
                ("target_amount", "target_amount_cents"),
                ("monthly_income", "monthly_income_cents"),
                ("fixed_expenses", "fixed_expenses_cents"),
                ("minimum_living_cost", "minimum_living_cost_cents"),
                ("saved_amount", "saved_amount_cents"),
            ]:
                if getattr(plan, cents_attr) is None:
                    setattr(plan, cents_attr, to_cents(getattr(plan, yuan_attr)))
                    migrated_plan_fields += 1

        db.commit()
        print(
            "  Migration complete. "
            f"{len(rows)} expenses and {migrated_plan_fields} plan fields updated."
        )

        remaining_expenses = db.query(Expense).filter(Expense.amount_cents.is_(None)).count()
        remaining_plan_fields = 0
        for plan in db.query(SavingPlan).all():
            remaining_plan_fields += sum(
                1
                for attr in [
                    "target_amount_cents",
                    "monthly_income_cents",
                    "fixed_expenses_cents",
                    "minimum_living_cost_cents",
                    "saved_amount_cents",
                ]
                if getattr(plan, attr) is None
            )
        print(f"  Remaining expenses without amount_cents: {remaining_expenses}")
        print(f"  Remaining plan money fields without cents: {remaining_plan_fields}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
