import datetime as dt

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import Language


class MediaLog(Base):
    __tablename__ = "media_log"
    __table_args__ = (
        CheckConstraint("duration_minutes >= 0", name="ck_media_log_duration_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False, length=2, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    media_type: Mapped[str] = mapped_column(String, nullable=False, default="drama")
    watched_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
