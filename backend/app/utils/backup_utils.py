"""Backup and restore utilities for the SQLite database."""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

REQUIRED_TABLE_COLUMNS: dict[str, set[str]] = {
    "expenses": {"id", "amount", "note", "date", "category"},
    "saving_plans": {
        "id",
        "target_amount",
        "deadline",
        "monthly_income",
        "fixed_expenses",
        "minimum_living_cost",
    },
}


def get_db_path() -> Path:
    """Return the current database file path."""
    from app.database import SQLALCHEMY_DATABASE_URL

    url = make_url(SQLALCHEMY_DATABASE_URL)
    if url.drivername != "sqlite" or url.database in (None, "", ":memory:"):
        raise ValueError("数据库备份仅支持文件型 SQLite 数据库")

    return Path(url.database).expanduser().resolve()


def validate_sqlite_backup(source_path: Path) -> None:
    """Validate that a restore candidate is an intact SaveMoney SQLite database."""
    if not source_path.exists():
        raise FileNotFoundError(f"备份文件不存在: {source_path}")
    if source_path.stat().st_size == 0:
        raise ValueError("备份文件为空")

    try:
        connection = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise ValueError("备份文件不是有效的 SQLite 数据库") from exc

    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise ValueError("SQLite integrity_check 未通过")

        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        missing_tables = sorted(set(REQUIRED_TABLE_COLUMNS) - tables)
        if missing_tables:
            raise ValueError(f"备份缺少必要表: {', '.join(missing_tables)}")

        for table_name, required_columns in REQUIRED_TABLE_COLUMNS.items():
            columns = {
                row[1]
                for row in connection.execute(
                    f"PRAGMA table_info({table_name})"
                ).fetchall()
            }
            missing_columns = sorted(required_columns - columns)
            if missing_columns:
                raise ValueError(
                    f"备份表 {table_name} 缺少必要字段: {', '.join(missing_columns)}"
                )
    except sqlite3.DatabaseError as exc:
        raise ValueError("备份文件不是有效的 SQLite 数据库") from exc
    finally:
        connection.close()


def create_backup() -> Path:
    """Create a timestamped backup copy of the database. Returns the backup path."""
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / f"savemoney_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


def restore_from_file(source_path: Path) -> None:
    """Replace the current database with the given file."""
    db_path = get_db_path()
    validate_sqlite_backup(source_path)
    shutil.copy2(source_path, db_path)
