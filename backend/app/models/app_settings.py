from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AppSettings(Base):
    """Single-row table (fixed id=1) for global app preferences.
    Single-machine, single-user tool — no need for multiple settings profiles."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    daily_new_card_limit: Mapped[int] = mapped_column(Integer, nullable=False)
