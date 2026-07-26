import csv
import datetime as dt
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import Language
from app.models.media_log import MediaLog
from app.models.subtitle_line import SubtitleLine
from app.schemas.media_log import (
    MediaLogCreate,
    MediaLogImportResult,
    MediaLogImportRowError,
    MediaLogRead,
    MediaLogUpdate,
)
from app.schemas.subtitle_line import SubtitleLineRead, SubtitleUploadResult
from app.services.srt_parser import SrtParseError, parse_srt

router = APIRouter(prefix="/media-logs", tags=["media-logs"])

MAX_SUBTITLE_FILE_SIZE = 2 * 1024 * 1024
MAX_CSV_FILE_SIZE = 5 * 1024 * 1024
MEDIA_LOG_CSV_COLUMNS = [
    "language",
    "title",
    "media_type",
    "watched_date",
    "duration_minutes",
    "notes",
]


def _get_or_404(db: Session, media_log_id: int) -> MediaLog:
    media_log = db.get(MediaLog, media_log_id)
    if media_log is None:
        raise HTTPException(status_code=404, detail="Media log not found")
    return media_log


@router.post("", response_model=MediaLogRead, status_code=201)
def create_media_log(payload: MediaLogCreate, db: Session = Depends(get_db)) -> MediaLog:
    media_log = MediaLog(**payload.model_dump())
    db.add(media_log)
    db.commit()
    db.refresh(media_log)
    return media_log


@router.get("", response_model=list[MediaLogRead])
def list_media_logs(
    language: Language,
    title: str | None = None,
    media_type: str | None = None,
    watched_date_from: dt.date | None = None,
    watched_date_to: dt.date | None = None,
    db: Session = Depends(get_db),
) -> list[MediaLog]:
    query = db.query(MediaLog).filter(MediaLog.language == language)
    if title is not None:
        query = query.filter(MediaLog.title.ilike(f"%{title}%"))
    if media_type is not None:
        query = query.filter(MediaLog.media_type == media_type)
    if watched_date_from is not None:
        query = query.filter(MediaLog.watched_date >= watched_date_from)
    if watched_date_to is not None:
        query = query.filter(MediaLog.watched_date <= watched_date_to)
    return query.order_by(MediaLog.watched_date.desc()).all()


def _format_import_row_error(exc: ValidationError | HTTPException | TypeError) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    if isinstance(exc, TypeError):
        return f"格式錯誤：{exc}"
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"])
    return f"{field}: {first['msg']}"


@router.post("/import-csv", response_model=MediaLogImportResult)
async def import_media_logs_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> MediaLogImportResult:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="僅接受 .csv 檔案")

    raw = await file.read(MAX_CSV_FILE_SIZE + 1)
    if len(raw) > MAX_CSV_FILE_SIZE:
        raise HTTPException(status_code=422, detail="檔案過大（上限 5MB）")

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="檔案編碼需為 UTF-8") from exc

    reader = csv.DictReader(io.StringIO(content))

    errors: list[MediaLogImportRowError] = []
    pending: list[MediaLog] = []
    for row_number, row in enumerate(reader, start=2):  # header occupies row 1
        if row.pop(None, None) is not None:  # DictReader's restkey: extra columns present
            errors.append(
                MediaLogImportRowError(
                    row=row_number, message="欄位數與表頭不符（該列欄位數過多）"
                )
            )
            continue

        cleaned = {key: (value if value not in (None, "") else None) for key, value in row.items()}
        try:
            payload = MediaLogCreate(**cleaned)
        except (ValidationError, HTTPException, TypeError) as exc:
            errors.append(
                MediaLogImportRowError(row=row_number, message=_format_import_row_error(exc))
            )
            continue

        pending.append(MediaLog(**payload.model_dump()))

    db.add_all(pending)
    db.commit()

    return MediaLogImportResult(created=len(pending), skipped=len(errors), errors=errors)


_CSV_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value: str) -> str:
    """Prefix a leading quote if value could be interpreted as a formula by spreadsheet
    software (Excel/LibreOffice/Sheets) when the exported file is opened there."""
    if value and value[0] in _CSV_FORMULA_TRIGGER_CHARS:
        return "'" + value
    return value


@router.get("/export-csv", response_class=Response)
def export_media_logs_csv(language: Language, db: Session = Depends(get_db)) -> Response:
    media_logs = (
        db.query(MediaLog)
        .filter(MediaLog.language == language)
        .order_by(MediaLog.watched_date.desc())
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(MEDIA_LOG_CSV_COLUMNS)
    for log in media_logs:
        writer.writerow(
            [
                log.language.value,
                _csv_safe(log.title),
                _csv_safe(log.media_type),
                log.watched_date.isoformat(),
                log.duration_minutes,
                _csv_safe(log.notes or ""),
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="media_logs_export_{language.value}.csv"'
        },
    )


@router.get("/{media_log_id}", response_model=MediaLogRead)
def get_media_log(media_log_id: int, db: Session = Depends(get_db)) -> MediaLog:
    return _get_or_404(db, media_log_id)


@router.patch("/{media_log_id}", response_model=MediaLogRead)
def update_media_log(
    media_log_id: int, payload: MediaLogUpdate, db: Session = Depends(get_db)
) -> MediaLog:
    media_log = _get_or_404(db, media_log_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(media_log, field, value)
    db.commit()
    db.refresh(media_log)
    return media_log


@router.delete("/{media_log_id}", status_code=204)
def delete_media_log(media_log_id: int, db: Session = Depends(get_db)) -> None:
    media_log = _get_or_404(db, media_log_id)
    db.delete(media_log)
    db.commit()


@router.post("/{media_log_id}/subtitles", response_model=SubtitleUploadResult)
async def upload_subtitles(
    media_log_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> SubtitleUploadResult:
    _get_or_404(db, media_log_id)

    if not file.filename or not file.filename.lower().endswith(".srt"):
        raise HTTPException(status_code=422, detail="僅接受 .srt 檔案")

    raw = await file.read(MAX_SUBTITLE_FILE_SIZE + 1)
    if len(raw) > MAX_SUBTITLE_FILE_SIZE:
        raise HTTPException(status_code=422, detail="檔案過大（上限 2MB）")

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="檔案編碼需為 UTF-8") from exc

    try:
        parsed_lines = parse_srt(content)
    except SrtParseError as exc:
        raise HTTPException(status_code=422, detail=f"SRT 格式錯誤：{exc}") from exc

    db.query(SubtitleLine).filter(SubtitleLine.media_log_id == media_log_id).delete()
    db.add_all(
        SubtitleLine(media_log_id=media_log_id, start_ms=start_ms, end_ms=end_ms, text=text)
        for start_ms, end_ms, text in parsed_lines
    )
    db.commit()

    return SubtitleUploadResult(media_log_id=media_log_id, line_count=len(parsed_lines))


@router.get("/{media_log_id}/subtitles", response_model=list[SubtitleLineRead])
def list_subtitles(media_log_id: int, db: Session = Depends(get_db)) -> list[SubtitleLine]:
    _get_or_404(db, media_log_id)
    return (
        db.query(SubtitleLine)
        .filter(SubtitleLine.media_log_id == media_log_id)
        .order_by(SubtitleLine.start_ms.asc())
        .all()
    )
