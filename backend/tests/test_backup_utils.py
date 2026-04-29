import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.utils.backup_utils import validate_sqlite_backup


class BackupUtilsTest(unittest.TestCase):
    def test_validate_sqlite_backup_rejects_non_sqlite_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "not-a-db.db"
            path.write_text("not sqlite", encoding="utf-8")

            with self.assertRaises(ValueError):
                validate_sqlite_backup(path)

    def test_validate_sqlite_backup_rejects_missing_core_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "wrong-schema.db"
            connection = sqlite3.connect(path)
            try:
                connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY)")
                connection.commit()
            finally:
                connection.close()

            with self.assertRaisesRegex(ValueError, "缺少必要表"):
                validate_sqlite_backup(path)

    def test_validate_sqlite_backup_accepts_legacy_core_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "savemoney.db"
            connection = sqlite3.connect(path)
            try:
                connection.execute(
                    """
                    CREATE TABLE expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount FLOAT NOT NULL,
                        note VARCHAR NOT NULL,
                        date DATE NOT NULL,
                        category VARCHAR NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE saving_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_amount FLOAT NOT NULL,
                        deadline DATE NOT NULL,
                        monthly_income FLOAT NOT NULL,
                        fixed_expenses FLOAT NOT NULL,
                        minimum_living_cost FLOAT NOT NULL
                    )
                    """
                )
                connection.commit()
            finally:
                connection.close()

            validate_sqlite_backup(path)


if __name__ == "__main__":
    unittest.main()
