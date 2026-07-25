import datetime as dt

from pydantic import BaseModel

from app.models.enums import DeArtikel, ReviewGrade


class ReviewSubmit(BaseModel):
    grade: ReviewGrade


class ReviewStats(BaseModel):
    reviewed_today: int
    accuracy_today: float | None
    streak_days: int


class ReviewHistoryDay(BaseModel):
    date: dt.date
    reviewed_count: int
    correct_count: int


class ArtikelQuizSubmit(BaseModel):
    answer: DeArtikel


class ArtikelQuizResult(BaseModel):
    correct: bool
    correct_answer: DeArtikel
