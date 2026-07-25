from pydantic import BaseModel

from app.models.enums import DeArtikel, ReviewGrade


class ReviewSubmit(BaseModel):
    grade: ReviewGrade


class ReviewStats(BaseModel):
    reviewed_today: int
    accuracy_today: float | None
    streak_days: int


class ArtikelQuizSubmit(BaseModel):
    answer: DeArtikel


class ArtikelQuizResult(BaseModel):
    correct: bool
    correct_answer: DeArtikel
