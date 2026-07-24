from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.enums import Language, ReviewGrade
from app.models.review_log import ReviewLog
from app.models.vocabulary import Vocabulary
from app.schemas.review import ReviewStats
from app.schemas.vocabulary import VocabularyRead

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _today_bounds() -> tuple[datetime, datetime]:
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
def get_review_queue(language: Language, db: Session = Depends(get_db)) -> list[Vocabulary]:
    now = datetime.utcnow()

    due_cards = (
        db.query(Vocabulary)
        .filter(
            Vocabulary.language == language,
            Vocabulary.srs_last_reviewed_at.is_not(None),
            Vocabulary.srs_next_review_at <= now,
        )
        .order_by(Vocabulary.srs_next_review_at.asc())
        .all()
    )

    settings = get_settings()
    new_cards_introduced_today = _count_new_cards_introduced_today(db, language)
    remaining_new_card_slots = max(
        0, settings.daily_new_card_limit - new_cards_introduced_today
    )

    new_cards: list[Vocabulary] = []
    if remaining_new_card_slots > 0:
        new_cards = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.language == language,
                Vocabulary.srs_last_reviewed_at.is_(None),
            )
            .order_by(Vocabulary.id.asc())
            .limit(remaining_new_card_slots)
            .all()
        )

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
