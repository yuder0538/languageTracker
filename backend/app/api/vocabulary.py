import csv
import datetime as dt
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import Language, ReviewGrade
from app.models.media_log import MediaLog
from app.models.review_log import ReviewLog
from app.models.subtitle_line import SubtitleLine
from app.models.vocabulary import Vocabulary
from app.schemas.review import ArtikelQuizResult, ArtikelQuizSubmit, ReviewSubmit
from app.schemas.vocabulary import (
    VocabularyCreate,
    VocabularyImportResult,
    VocabularyImportRowError,
    VocabularyRead,
    VocabularyUpdate,
    validate_language_specific_fields,
)
from app.services.anki_export import build_anki_line
from app.services.de_translation import (
    TranslationApiError,
    fetch_de_to_zh_translation,
    fetch_en_to_zh_translation,
)
from app.services.en_dictionary import DictionaryLookupError, fetch_en_dictionary_data
from app.services.http_client import ExternalApiError
from app.services.srs import SrsState, schedule_next_review

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


def _get_or_404(db: Session, vocabulary_id: int) -> Vocabulary:
    vocabulary = db.get(Vocabulary, vocabulary_id)
    if vocabulary is None:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")
    return vocabulary


def _validate_media_log_language(db: Session, media_log_id: int, language: Language) -> None:
    media_log = db.get(MediaLog, media_log_id)
    if media_log is None:
        raise HTTPException(
            status_code=422, detail="media_log_id does not reference an existing media log"
        )
    if media_log.language != language:
        raise HTTPException(
            status_code=422,
            detail="media_log_id references a media log in a different language",
        )


@router.post("", response_model=VocabularyRead, status_code=201)
def create_vocabulary(payload: VocabularyCreate, db: Session = Depends(get_db)) -> Vocabulary:
    if payload.media_log_id is not None:
        _validate_media_log_language(db, payload.media_log_id, payload.language)

    vocabulary = Vocabulary(**payload.model_dump())
    db.add(vocabulary)
    db.commit()
    db.refresh(vocabulary)
    return vocabulary


MAX_CSV_FILE_SIZE = 5 * 1024 * 1024


def _format_import_row_error(exc: ValidationError | HTTPException | TypeError) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    if isinstance(exc, TypeError):
        return f"格式錯誤：{exc}"
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"])
    return f"{field}: {first['msg']}"


@router.post("/import-csv", response_model=VocabularyImportResult)
async def import_vocabulary_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> VocabularyImportResult:
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

    errors: list[VocabularyImportRowError] = []
    pending: list[Vocabulary] = []
    for row_number, row in enumerate(reader, start=2):  # header occupies row 1
        if row.pop(None, None) is not None:  # DictReader's restkey: extra columns present
            errors.append(
                VocabularyImportRowError(
                    row=row_number, message="欄位數與表頭不符（該列欄位數過多）"
                )
            )
            continue
        cleaned = {key: (value if value not in (None, "") else None) for key, value in row.items()}
        try:
            payload = VocabularyCreate(**cleaned)
            if payload.media_log_id is not None:
                _validate_media_log_language(db, payload.media_log_id, payload.language)
        except (ValidationError, HTTPException, TypeError) as exc:
            errors.append(
                VocabularyImportRowError(row=row_number, message=_format_import_row_error(exc))
            )
            continue

        pending.append(Vocabulary(**payload.model_dump()))

    db.add_all(pending)
    db.commit()

    return VocabularyImportResult(created=len(pending), skipped=len(errors), errors=errors)


@router.get("", response_model=list[VocabularyRead])
def list_vocabulary(
    language: Language,
    headword: str | None = None,
    media_log_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Vocabulary]:
    query = db.query(Vocabulary).filter(Vocabulary.language == language)
    if headword is not None:
        query = query.filter(Vocabulary.headword.ilike(f"%{headword}%"))
    if media_log_id is not None:
        query = query.filter(Vocabulary.media_log_id == media_log_id)
    return query.order_by(Vocabulary.headword.asc()).all()


@router.get("/export/anki", response_class=Response)
def export_vocabulary_anki(language: Language, db: Session = Depends(get_db)) -> Response:
    words = (
        db.query(Vocabulary)
        .filter(Vocabulary.language == language)
        .order_by(Vocabulary.headword.asc())
        .all()
    )
    content = "\n".join(build_anki_line(word) for word in words)

    return Response(
        content=content,
        media_type="text/tab-separated-values",
        headers={
            "Content-Disposition": f'attachment; filename="anki_export_{language.value}.txt"'
        },
    )


@router.get("/{vocabulary_id}", response_model=VocabularyRead)
def get_vocabulary(vocabulary_id: int, db: Session = Depends(get_db)) -> Vocabulary:
    return _get_or_404(db, vocabulary_id)


@router.patch("/{vocabulary_id}", response_model=VocabularyRead)
def update_vocabulary(
    vocabulary_id: int, payload: VocabularyUpdate, db: Session = Depends(get_db)
) -> Vocabulary:
    vocabulary = _get_or_404(db, vocabulary_id)
    updates = payload.model_dump(exclude_unset=True)

    effective_ipa = updates.get("ipa", vocabulary.ipa)
    effective_de_artikel = updates.get("de_artikel", vocabulary.de_artikel)
    effective_de_plural = updates.get("de_plural", vocabulary.de_plural)
    effective_de_conjugation = updates.get("de_conjugation", vocabulary.de_conjugation)

    try:
        validate_language_specific_fields(
            vocabulary.language,
            effective_ipa,
            effective_de_artikel,
            effective_de_plural,
            effective_de_conjugation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if "media_log_id" in updates and updates["media_log_id"] is not None:
        _validate_media_log_language(db, updates["media_log_id"], vocabulary.language)

    for field, value in updates.items():
        setattr(vocabulary, field, value)
    db.commit()
    db.refresh(vocabulary)
    return vocabulary


@router.post("/{vocabulary_id}/enrich/en-dictionary", response_model=VocabularyRead)
def enrich_en_dictionary(vocabulary_id: int, db: Session = Depends(get_db)) -> Vocabulary:
    vocabulary = _get_or_404(db, vocabulary_id)
    if vocabulary.language != Language.EN:
        raise HTTPException(status_code=422, detail="僅適用英文單字（language 必須為 'en'）")

    try:
        data = fetch_en_dictionary_data(vocabulary.headword)
    except DictionaryLookupError as exc:
        raise HTTPException(status_code=502, detail=f"字典查無此字：{exc}") from exc
    except ExternalApiError as exc:
        raise HTTPException(status_code=502, detail=f"外部字典服務暫時無法連線：{exc}") from exc

    try:
        translation = fetch_en_to_zh_translation(vocabulary.headword)
    except TranslationApiError as exc:
        raise HTTPException(status_code=502, detail=f"翻譯服務回應異常：{exc}") from exc
    except ExternalApiError as exc:
        raise HTTPException(status_code=502, detail=f"外部翻譯服務暫時無法連線：{exc}") from exc

    vocabulary.ipa = data.ipa
    vocabulary.en_definition = data.definition
    vocabulary.translation_zh = translation
    if not vocabulary.part_of_speech and data.part_of_speech:
        vocabulary.part_of_speech = data.part_of_speech

    db.commit()
    db.refresh(vocabulary)
    return vocabulary


@router.post("/{vocabulary_id}/enrich/de-translation", response_model=VocabularyRead)
def enrich_de_translation(vocabulary_id: int, db: Session = Depends(get_db)) -> Vocabulary:
    vocabulary = _get_or_404(db, vocabulary_id)
    if vocabulary.language != Language.DE:
        raise HTTPException(status_code=422, detail="僅適用德文單字（language 必須為 'de'）")

    try:
        translation = fetch_de_to_zh_translation(vocabulary.headword)
    except TranslationApiError as exc:
        raise HTTPException(status_code=502, detail=f"翻譯服務回應異常：{exc}") from exc
    except ExternalApiError as exc:
        raise HTTPException(status_code=502, detail=f"外部翻譯服務暫時無法連線：{exc}") from exc

    vocabulary.translation_zh = translation
    db.commit()
    db.refresh(vocabulary)
    return vocabulary


@router.post("/{vocabulary_id}/enrich/example-sentence", response_model=VocabularyRead)
def enrich_example_sentence(vocabulary_id: int, db: Session = Depends(get_db)) -> Vocabulary:
    vocabulary = _get_or_404(db, vocabulary_id)

    if vocabulary.media_log_id is None:
        raise HTTPException(
            status_code=422, detail="此單字未關聯劇集紀錄，無法對齊例句"
        )

    has_subtitles = (
        db.query(SubtitleLine)
        .filter(SubtitleLine.media_log_id == vocabulary.media_log_id)
        .first()
        is not None
    )
    if not has_subtitles:
        raise HTTPException(status_code=422, detail="該劇集尚未上傳字幕")

    matching_line = (
        db.query(SubtitleLine)
        .filter(
            SubtitleLine.media_log_id == vocabulary.media_log_id,
            SubtitleLine.text.ilike(f"%{vocabulary.headword}%"),
        )
        .first()
    )
    if matching_line is None:
        raise HTTPException(status_code=404, detail="字幕中找不到此單字")

    vocabulary.example_sentence = matching_line.text
    db.commit()
    db.refresh(vocabulary)
    return vocabulary


MAX_SRS_INTERVAL_DAYS = 365 * 100  # 100 years; well beyond any real review need,
# and far short of datetime/timedelta's own limits, so `now + timedelta(days=...)`
# below can never raise OverflowError even after many uncapped ease-factor reviews.


def _apply_review_grade(db: Session, vocabulary: Vocabulary, grade: ReviewGrade) -> Vocabulary:
    current_state = SrsState(
        interval_days=vocabulary.srs_interval_days,
        ease_factor=vocabulary.srs_ease_factor,
        repetitions=vocabulary.srs_repetitions,
        lapses=vocabulary.srs_lapses,
    )
    new_state = schedule_next_review(current_state, grade)
    interval_days = min(new_state.interval_days, MAX_SRS_INTERVAL_DAYS)

    now = dt.datetime.utcnow()
    vocabulary.srs_interval_days = interval_days
    vocabulary.srs_ease_factor = new_state.ease_factor
    vocabulary.srs_repetitions = new_state.repetitions
    vocabulary.srs_lapses = new_state.lapses
    vocabulary.srs_next_review_at = now + dt.timedelta(days=interval_days)
    vocabulary.srs_last_reviewed_at = now

    db.add(
        ReviewLog(
            vocabulary_id=vocabulary.id,
            reviewed_at=now,
            grade=grade,
            interval_days_after=interval_days,
        )
    )
    db.commit()
    db.refresh(vocabulary)
    return vocabulary


@router.post("/{vocabulary_id}/review", response_model=VocabularyRead)
def submit_review(
    vocabulary_id: int, payload: ReviewSubmit, db: Session = Depends(get_db)
) -> Vocabulary:
    vocabulary = _get_or_404(db, vocabulary_id)
    return _apply_review_grade(db, vocabulary, payload.grade)


@router.post("/{vocabulary_id}/review/artikel-quiz", response_model=ArtikelQuizResult)
def submit_artikel_quiz(
    vocabulary_id: int, payload: ArtikelQuizSubmit, db: Session = Depends(get_db)
) -> ArtikelQuizResult:
    vocabulary = _get_or_404(db, vocabulary_id)
    if vocabulary.language != Language.DE or vocabulary.de_artikel is None:
        raise HTTPException(
            status_code=422, detail="此單字不適用冠詞填空（非德文名詞或未標註冠詞）"
        )

    correct_answer = vocabulary.de_artikel
    correct = payload.answer == correct_answer
    grade = ReviewGrade.GOOD if correct else ReviewGrade.AGAIN
    _apply_review_grade(db, vocabulary, grade)

    return ArtikelQuizResult(correct=correct, correct_answer=correct_answer)


@router.delete("/{vocabulary_id}", status_code=204)
def delete_vocabulary(vocabulary_id: int, db: Session = Depends(get_db)) -> None:
    vocabulary = _get_or_404(db, vocabulary_id)
    db.delete(vocabulary)
    db.commit()
