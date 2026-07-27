import random
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import Language, ReviewGrade
from app.models.review_log import ReviewLog
from app.models.vocabulary import Vocabulary
from app.schemas.review import ReviewHistoryDay, ReviewStats
from app.schemas.vocabulary import VocabularyRead
from app.services.app_settings import get_app_settings

MAX_HISTORY_DAYS = 90

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _today_bounds() -> tuple[datetime, datetime]:
    # Uses server local time, matching the `datetime.now()` timestamps written
    # in vocabulary.py/_apply_review_grade and the `now` below — mixing this
    # with UTC caused "today" to be wrong for hours around local midnight.
    today_start = datetime.combine(date.today(), datetime.min.time())
    return today_start, today_start + timedelta(days=1)


def _count_new_cards_introduced_today(db: Session, language: Language) -> int:
    today_start, today_end = _today_bounds()

    first_review_subq = (
        db.query(
            ReviewLog.vocabulary_id.label("vocabulary_id"),
            func.min(ReviewLog.reviewed_at).label("first_reviewed_at"),
        )
        .group_by(ReviewLog.vocabulary_id)
        .subquery()
    )

    count = (
        db.query(func.count())
        .select_from(first_review_subq)
        .join(Vocabulary, Vocabulary.id == first_review_subq.c.vocabulary_id)
        .filter(
            Vocabulary.language == language,
            first_review_subq.c.first_reviewed_at >= today_start,
            first_review_subq.c.first_reviewed_at < today_end,
        )
        .scalar()
    )
    return count or 0


@router.get("/queue", response_model=list[VocabularyRead])
def get_review_queue(
    language: Language,
    card_type: Literal["standard", "artikel"] = "standard",
    db: Session = Depends(get_db),
) -> list[Vocabulary]:
    if card_type == "artikel" and language == Language.EN:
        raise HTTPException(
            status_code=422, detail="英文沒有冠詞，不適用冠詞填空模式"
        )

    now = datetime.now()

    due_query = db.query(Vocabulary).filter(
        Vocabulary.language == language,
        Vocabulary.srs_last_reviewed_at.is_not(None),
        Vocabulary.srs_next_review_at <= now,
    )
    if card_type == "artikel":
        due_query = due_query.filter(Vocabulary.de_artikel.is_not(None))
    due_cards = due_query.all()
    random.shuffle(due_cards)

    app_settings = get_app_settings(db)
    new_cards_introduced_today = _count_new_cards_introduced_today(db, language)
    remaining_new_card_slots = max(
        0, app_settings.daily_new_card_limit - new_cards_introduced_today
    )

    new_cards: list[Vocabulary] = []
    if remaining_new_card_slots > 0:
        new_query = db.query(Vocabulary).filter(
            Vocabulary.language == language,
            Vocabulary.srs_last_reviewed_at.is_(None),
        )
        if card_type == "artikel":
            new_query = new_query.filter(Vocabulary.de_artikel.is_not(None))
        new_cards = new_query.order_by(Vocabulary.id.asc()).limit(
            remaining_new_card_slots
        ).all()

    return due_cards + new_cards


@router.get("/stats", response_model=ReviewStats)
def get_review_stats(language: Language, db: Session = Depends(get_db)) -> ReviewStats:
    today_start, today_end = _today_bounds()

    today_grades = (
        db.query(ReviewLog.grade)
        .join(Vocabulary, Vocabulary.id == ReviewLog.vocabulary_id)
        .filter(
            Vocabulary.language == language,
            ReviewLog.reviewed_at >= today_start,
            ReviewLog.reviewed_at < today_end,
        )
        .all()
    )
    reviewed_today = len(today_grades)
    accuracy_today = None
    if reviewed_today > 0:
        correct = sum(1 for (grade,) in today_grades if grade != ReviewGrade.AGAIN)
        accuracy_today = correct / reviewed_today

    reviewed_days = {
        row.day
        for row in db.query(func.date(ReviewLog.reviewed_at).label("day"))
        .join(Vocabulary, Vocabulary.id == ReviewLog.vocabulary_id)
        .filter(Vocabulary.language == language)
        .distinct()
        .all()
    }

    cursor = date.today()
    if cursor.isoformat() not in reviewed_days:
        cursor -= timedelta(days=1)

    streak_days = 0
    while cursor.isoformat() in reviewed_days:
        streak_days += 1
        cursor -= timedelta(days=1)

    return ReviewStats(
        reviewed_today=reviewed_today,
        accuracy_today=accuracy_today,
        streak_days=streak_days,
    )


@router.get("/history", response_model=list[ReviewHistoryDay])
def get_review_history(
    language: Language,
    days: int = 35,
    db: Session = Depends(get_db),
) -> list[ReviewHistoryDay]:
    """Daily review counts for the trailing `days` days (oldest first, today last),
    including zero-count days. Powers the Dashboard's review-calendar heatmap and
    multi-day accuracy trend (a single endpoint backs both, one source of truth)."""
    if days < 1 or days > MAX_HISTORY_DAYS:
        raise HTTPException(
            status_code=422, detail=f"days 必須介於 1 到 {MAX_HISTORY_DAYS} 之間"
        )

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)

    rows = (
        db.query(
            func.date(ReviewLog.reviewed_at).label("day"),
            func.count().label("reviewed_count"),
            func.sum(case((ReviewLog.grade != ReviewGrade.AGAIN, 1), else_=0)).label(
                "correct_count"
            ),
        )
        .join(Vocabulary, Vocabulary.id == ReviewLog.vocabulary_id)
        .filter(
            Vocabulary.language == language,
            ReviewLog.reviewed_at >= start_dt,
            ReviewLog.reviewed_at < end_dt,
        )
        .group_by(func.date(ReviewLog.reviewed_at))
        .all()
    )
    counts_by_day = {row.day: (row.reviewed_count, row.correct_count or 0) for row in rows}

    result: list[ReviewHistoryDay] = []
    cursor = start_date
    while cursor <= end_date:
        reviewed_count, correct_count = counts_by_day.get(cursor.isoformat(), (0, 0))
        result.append(
            ReviewHistoryDay(
                date=cursor, reviewed_count=reviewed_count, correct_count=correct_count
            )
        )
        cursor += timedelta(days=1)
    return result
