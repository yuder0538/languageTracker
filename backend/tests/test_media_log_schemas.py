import datetime as dt

import pytest
from pydantic import ValidationError

from app.models.enums import Language
from app.schemas.media_log import MediaLogCreate


def test_media_log_create_defaults_media_type():
    payload = MediaLogCreate(
        language=Language.EN,
        title="Friends",
        watched_date=dt.date(2026, 1, 1),
        duration_minutes=25,
    )
    assert payload.media_type == "drama"


def test_media_log_create_rejects_negative_duration():
    with pytest.raises(ValidationError):
        MediaLogCreate(
            language=Language.EN,
            title="Friends",
            watched_date=dt.date(2026, 1, 1),
            duration_minutes=-1,
        )


def test_media_log_create_rejects_empty_title():
    with pytest.raises(ValidationError):
        MediaLogCreate(
            language=Language.EN,
            title="",
            watched_date=dt.date(2026, 1, 1),
            duration_minutes=10,
        )
