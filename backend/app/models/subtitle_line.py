from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SubtitleLine(Base):
    __tablename__ = "subtitle_line"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    media_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("media_log.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
