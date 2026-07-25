import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import DeArtikel, Language

DE_CONJUGATION_MAX_LENGTH = 2000


def validate_language_specific_fields(
    language: Language,
    ipa: str | None,
    de_artikel: DeArtikel | None,
    de_plural: str | None,
    de_conjugation: str | None,
) -> None:
    if language == Language.EN:
        if de_artikel is not None or de_plural is not None or de_conjugation is not None:
            raise ValueError(
                "de_artikel/de_plural/de_conjugation are only allowed when language='de'"
            )
    elif language == Language.DE:
        if ipa is not None:
            raise ValueError("ipa is only allowed when language='en'")


class VocabularyCreate(BaseModel):
    language: Language
    headword: str = Field(min_length=1)
    part_of_speech: str | None = None
    translation_zh: str | None = None
    example_sentence: str | None = None
    media_log_id: int | None = None

    ipa: str | None = None
    de_artikel: DeArtikel | None = None
    de_plural: str | None = None
    de_conjugation: str | None = Field(default=None, max_length=DE_CONJUGATION_MAX_LENGTH)

    notes: str | None = None

    @model_validator(mode="after")
    def _check_language_specific_fields(self) -> "VocabularyCreate":
        validate_language_specific_fields(
            self.language, self.ipa, self.de_artikel, self.de_plural, self.de_conjugation
        )
        return self


class VocabularyUpdate(BaseModel):
    """`language` is intentionally omitted: it is immutable after creation.
    Cross-field EN/DE validation for the merged (existing + updated) state is
    performed in the router, since this schema alone doesn't know the record's
    current language."""

    headword: str | None = Field(default=None, min_length=1)
    part_of_speech: str | None = None
    translation_zh: str | None = None
    example_sentence: str | None = None
    media_log_id: int | None = None

    ipa: str | None = None
    de_artikel: DeArtikel | None = None
    de_plural: str | None = None
    de_conjugation: str | None = Field(default=None, max_length=DE_CONJUGATION_MAX_LENGTH)

    notes: str | None = None


class VocabularyImportRowError(BaseModel):
    row: int
    message: str


class VocabularyImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[VocabularyImportRowError]


class VocabularyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language: Language
    headword: str
    part_of_speech: str | None
    translation_zh: str | None
    example_sentence: str | None
    media_log_id: int | None
    ipa: str | None
    en_definition: str | None
    de_artikel: DeArtikel | None
    de_plural: str | None
    de_conjugation: str | None
    notes: str | None
    created_at: dt.datetime
    updated_at: dt.datetime
