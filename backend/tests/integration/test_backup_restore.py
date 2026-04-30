import shutil
import sqlite3
from pathlib import Path


def test_backup_uses_configured_sqlite_database_path(db_path) -> None:
    from app.utils.backup_utils import get_db_path

    assert get_db_path() == db_path.resolve()


def test_restore_db_replaces_configured_sqlite_database(api_client, db_path, tmp_path) -> None:
    from app.database import engine

    original_backup = tmp_path / "original_before_restore.db"
    restore_source = tmp_path / "restore_source.db"
    shutil.copy2(db_path, original_backup)
    shutil.copy2(db_path, restore_source)

    connection = sqlite3.connect(restore_source)
    try:
        connection.execute("CREATE TABLE restored_marker (value TEXT NOT NULL)")
        connection.execute("INSERT INTO restored_marker (value) VALUES ('ok')")
        connection.commit()
    finally:
        connection.close()

    try:
        with restore_source.open("rb") as restore_file:
            response = api_client.post(
                "/backup/restore-db",
                files={
                    "file": (
                        "restore_source.db",
                        restore_file,
                        "application/octet-stream",
                    )
                },
            )

        assert response.status_code == 200

        restored = sqlite3.connect(db_path)
        try:
            marker = restored.execute("SELECT value FROM restored_marker").fetchone()
        finally:
            restored.close()
        assert marker == ("ok",)
    finally:
        engine.dispose()
        shutil.copy2(original_backup, db_path)
