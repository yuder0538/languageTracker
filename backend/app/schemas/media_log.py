import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Language


class MediaLogCreate(BaseModel):
    language: Language
    title: str = Field(min_length=1)
    media_type: str = "drama"
    watched_date: dt.date
    duration_minutes: int = Field(ge=0)
    notes: str | None = None


class MediaLogUpdate(BaseModel):
    """`language` is intentionally omitted: it is immutable after creation and any
    `language` field in the request body is silently ignored (pydantic's default
    `extra="ignore"` behavior)."""

    title: str | None = Field(default=None, min_length=1)
    media_type: str | None = None
    watched_date: dt.date | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None


class MediaLogImportRowError(BaseModel):
    row: int
    message: str


class MediaLogImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[MediaLogImportRowError]


class MediaLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language: Language
    title: str
    media_type: str
    watched_date: dt.date
    duration_minutes: int
    notes: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
