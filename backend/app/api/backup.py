import os
import sqlite3
import tempfile
from collections.abc import Callable
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from app.core.config import get_settings
from app.core.db import engine
from app.schemas.backup import RestoreResult

router = APIRouter(prefix="/backup", tags=["backup"])

SQLITE_URL_PREFIX = "sqlite:///"
SQLITE_MAGIC_HEADER = b"SQLite format 3\x00"
REQUIRED_RESTORE_TABLES = {"vocabulary", "media_log", "alembic_version"}
MAX_RESTORE_FILE_SIZE = 50 * 1024 * 1024


def sqlite_path_from_url(database_url: str) -> str:
    if not database_url.startswith(SQLITE_URL_PREFIX):
        raise ValueError(f"Unsupported database_url for backup/restore: {database_url}")
    return database_url[len(SQLITE_URL_PREFIX) :]


def create_backup_file(
    source_path: str,
    dest_path: str,
    pages: int = -1,
    progress: Callable[[int, int, int], None] | None = None,
) -> None:
    """Hot-copy a SQLite database via the official backup API (not a raw byte copy,
    which could snapshot a write in progress and produce a corrupt file)."""
    source = sqlite3.connect(source_path)
    try:
        dest = sqlite3.connect(dest_path)
        try:
            source.backup(dest, pages=pages, progress=progress)
        finally:
            dest.close()
    finally:
        source.close()


@router.get("/export", response_class=FileResponse)
def export_backup() -> FileResponse:
    settings = get_settings()
    source_path = sqlite_path_from_url(settings.database_url)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="資料庫檔案尚未建立，無法備份")

    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        create_backup_file(source_path, tmp_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"immersion_tracker_backup_{timestamp}.db"

        return FileResponse(
            tmp_path,
            media_type="application/octet-stream",
            filename=filename,
            background=BackgroundTask(os.remove, tmp_path),
        )
    except BaseException:
        os.remove(tmp_path)
        raise


def _validate_restore_upload(raw: bytes) -> None:
    if not raw.startswith(SQLITE_MAGIC_HEADER):
        raise HTTPException(status_code=422, detail="檔案不是合法的資料庫備份檔")

    fd, tmp_check_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        with open(tmp_check_path, "wb") as f:
            f.write(raw)
        conn = sqlite3.connect(tmp_check_path)
        try:
            tables = {
                row[0]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()
    finally:
        os.remove(tmp_check_path)

    missing = REQUIRED_RESTORE_TABLES - tables
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"檔案不是合法的資料庫備份檔（缺少資料表：{', '.join(sorted(missing))}）",
        )


@router.post("/restore", response_model=RestoreResult)
async def restore_backup(
    confirm: bool = False, file: UploadFile = File(...)
) -> RestoreResult:
    if confirm is not True:
        raise HTTPException(
            status_code=422, detail="需要 confirm=true 才會執行還原，這是不可逆操作"
        )

    raw = await file.read(MAX_RESTORE_FILE_SIZE + 1)
    if len(raw) > MAX_RESTORE_FILE_SIZE:
        raise HTTPException(status_code=422, detail="檔案過大（上限 50MB）")

    _validate_restore_upload(raw)

    settings = get_settings()
    live_path = sqlite_path_from_url(settings.database_url)
    live_dir = os.path.dirname(live_path) or "."

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_backup_filename = f"immersion_tracker.before-restore-{timestamp}.db"
    safety_backup_path = os.path.join(live_dir, safety_backup_filename)
    # Pre-create with restrictive permissions: sqlite3.connect() on a fresh path
    # inherits the process umask (often world-readable), which would otherwise
    # leave a full database copy readable by other local users/processes.
    safety_fd = os.open(safety_backup_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(safety_fd)
    create_backup_file(live_path, safety_backup_path)

    engine.dispose()

    fd, tmp_upload_path = tempfile.mkstemp(suffix=".db", dir=live_dir)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        os.replace(tmp_upload_path, live_path)
    except BaseException:
        if os.path.exists(tmp_upload_path):
            os.remove(tmp_upload_path)
        raise

    return RestoreResult(restored=True, safety_backup_filename=safety_backup_filename)
