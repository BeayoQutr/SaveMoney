"""Backup and restore API routes."""

import csv
import io
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.database import SessionLocal
from app.schemas import ExpenseCreateRequest
from app.services.expense_service import create_expense
from app.utils.backup_utils import create_backup, get_db_path, restore_from_file

router = APIRouter(prefix="/backup", tags=["backup"])


@router.get("/download-db")
def download_db():
    """Download the entire SQLite database file."""
    db_path = get_db_path()
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="数据库文件不存在")
    return FileResponse(
        path=str(db_path),
        filename="savemoney.db",
        media_type="application/octet-stream",
    )


@router.post("/restore-db")
async def restore_db(file: UploadFile = File(...)):
    """Upload a SQLite database file to replace the current one.
    Creates an automatic backup before restoring."""
    # Create backup before restoring
    try:
        backup_path = create_backup()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动备份失败: {e}")

    # Save uploaded file to a temp location
    tmp_path: Path | None = None
    try:
        suffix = ".db"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        restore_from_file(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"恢复失败: {e}")
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    return {
        "message": "数据库恢复成功",
        "backup_path": str(backup_path),
    }


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)):
    """Import expenses from a CSV file. Creates a backup before importing."""
    # Create backup before import
    try:
        backup_path = create_backup()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动备份失败: {e}")

    try:
        content = await file.read()
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        imported = 0
        errors = []
        db = SessionLocal()
        try:
            for i, row in enumerate(reader, start=1):
                try:
                    amount = float(row.get("amount", 0))
                    note = row.get("note", "").strip()
                    expense_date = row.get("date", "").strip()
                    category = row.get("category", "").strip() or None

                    if not note or amount <= 0 or not expense_date:
                        errors.append(f"第{i}行: 数据不完整，跳过")
                        continue

                    data = ExpenseCreateRequest(
                        amount=amount,
                        note=note,
                        date=expense_date,
                        category=category,
                    )
                    create_expense(db, data)
                    imported += 1
                except Exception as e:
                    errors.append(f"第{i}行: {e}")
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV 解析失败: {e}")

    return {
        "message": f"导入完成: 成功 {imported} 条",
        "imported": imported,
        "errors": errors[:20],  # Limit error output
        "backup_path": str(backup_path),
    }
