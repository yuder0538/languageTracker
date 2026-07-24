import datetime as dt

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import DeArtikel, Language


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[Language] = mapped_column(
        Enum(Language, native_enum=False, length=2, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        index=True,
    )
    headword: Mapped[str] = mapped_column(String, nullable=False, index=True)
    part_of_speech: Mapped[str | None] = mapped_column(String, nullable=True)
    translation_zh: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)

    media_log_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("media_log.id", ondelete="SET NULL"), nullable=True
    )

    # 英文專屬
    ipa: Mapped[str | None] = mapped_column(String, nullable=True)
    en_definition: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 德文專屬
    de_artikel: Mapped[DeArtikel | None] = mapped_column(
        Enum(
            DeArtikel,
            native_enum=False,
            length=3,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=True,
    )
    de_plural: Mapped[str | None] = mapped_column(String, nullable=True)
    de_conjugation: Mapped[str | None] = mapped_column(Text, nullable=True)

    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    # SRS 排程狀態
    srs_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    srs_ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    srs_repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    srs_lapses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    srs_next_review_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    srs_last_reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
