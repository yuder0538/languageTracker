import pytest
from pydantic import ValidationError

from app.models.enums import DeArtikel, Language
from app.schemas.vocabulary import VocabularyCreate


def test_en_word_with_ipa_is_valid():
    payload = VocabularyCreate(language=Language.EN, headword="run", ipa="/rʌn/")
    assert payload.ipa == "/rʌn/"


def test_de_word_with_artikel_is_valid():
    payload = VocabularyCreate(
        language=Language.DE, headword="Haus", de_artikel=DeArtikel.DAS, de_plural="Häuser"
    )
    assert payload.de_artikel == DeArtikel.DAS


def test_en_word_rejects_de_artikel():
    with pytest.raises(ValidationError):
        VocabularyCreate(language=Language.EN, headword="run", de_artikel=DeArtikel.DER)


def test_de_word_rejects_ipa():
    with pytest.raises(ValidationError):
        VocabularyCreate(language=Language.DE, headword="Haus", ipa="/haus/")


def test_de_conjugation_length_limit():
    with pytest.raises(ValidationError):
        VocabularyCreate(
            language=Language.DE,
            headword="gehen",
            de_conjugation="x" * 2001,
        )
