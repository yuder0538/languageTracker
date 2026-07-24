import datetime as dt

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import Language
from app.models.media_log import MediaLog
from app.models.subtitle_line import SubtitleLine
from app.schemas.media_log import MediaLogCreate, MediaLogRead, MediaLogUpdate
from app.schemas.subtitle_line import SubtitleLineRead, SubtitleUploadResult
from app.services.srt_parser import SrtParseError, parse_srt

router = APIRouter(prefix="/media-logs", tags=["media-logs"])

MAX_SUBTITLE_FILE_SIZE = 2 * 1024 * 1024


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
    media_type: str | None = None,
    watched_date_from: dt.date | None = None,
    watched_date_to: dt.date | None = None,
    db: Session = Depends(get_db),
) -> list[MediaLog]:
    query = db.query(MediaLog).filter(MediaLog.language == language)
    if media_type is not None:
        query = query.filter(MediaLog.media_type == media_type)
    if watched_date_from is not None:
        query = query.filter(MediaLog.watched_date >= watched_date_from)
    if watched_date_to is not None:
        query = query.filter(MediaLog.watched_date <= watched_date_to)
    return query.order_by(MediaLog.watched_date.desc()).all()


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
