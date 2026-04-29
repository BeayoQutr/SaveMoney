"""Backup and restore utilities for the SQLite database."""

import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from app.database import SQLALCHEMY_DATABASE_URL


def get_db_path() -> Path:
    """Return the current database file path."""
    url = make_url(SQLALCHEMY_DATABASE_URL)
    if url.drivername != "sqlite" or url.database in (None, "", ":memory:"):
        raise ValueError("数据库备份仅支持文件型 SQLite 数据库")

    return Path(url.database).expanduser().resolve()


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
    if not source_path.exists():
        raise FileNotFoundError(f"备份文件不存在: {source_path}")
    shutil.copy2(source_path, db_path)
