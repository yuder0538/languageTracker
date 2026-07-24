from pydantic import BaseModel

from app.models.enums import ReviewGrade


class ReviewSubmit(BaseModel):
    grade: ReviewGrade


class ReviewStats(BaseModel):
    reviewed_today: int
    accuracy_today: float | None
    streak_days: int
