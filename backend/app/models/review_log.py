import datetime as dt

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import ReviewGrade


class ReviewLog(Base):
    __tablename__ = "review_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vocabulary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewed_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    grade: Mapped[ReviewGrade] = mapped_column(
        Enum(
            ReviewGrade,
            native_enum=False,
            length=5,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    interval_days_after: Mapped[int] = mapped_column(Integer, nullable=False)
