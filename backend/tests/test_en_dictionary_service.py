import httpx
import pytest

from app.services.en_dictionary import DictionaryLookupError, fetch_en_dictionary_data
from app.services.http_client import ExternalApiError


def _external_api_error_from(cause: BaseException) -> ExternalApiError:
    try:
        raise ExternalApiError("wrapped") from cause
    except ExternalApiError as exc:
        return exc


def test_fetch_extracts_ipa_definition_and_part_of_speech(monkeypatch):
    entries = [
        {
            "word": "hello",
            "phonetic": "/həˈloʊ/",
            "phonetics": [],
            "meanings": [
                {
                    "partOfSpeech": "exclamation",
                    "definitions": [{"definition": "used as a greeting"}],
                }
            ],
        }
    ]
    monkeypatch.setattr(
        "app.services.en_dictionary.get_json", lambda url, **kwargs: entries
    )

    result = fetch_en_dictionary_data("hello")

    assert result.ipa == "/həˈloʊ/"
    assert result.definition == "used as a greeting"
    assert result.part_of_speech == "exclamation"


def test_fetch_falls_back_to_phonetics_list_when_phonetic_missing(monkeypatch):
    entries = [
        {
            "word": "run",
            "phonetic": "",
            "phonetics": [{"text": ""}, {"text": "/rʌn/"}],
            "meanings": [
                {"partOfSpeech": "verb", "definitions": [{"definition": "to move fast"}]}
            ],
        }
    ]
    monkeypatch.setattr(
        "app.services.en_dictionary.get_json", lambda url, **kwargs: entries
    )

    result = fetch_en_dictionary_data("run")

    assert result.ipa == "/rʌn/"


def test_fetch_raises_lookup_error_on_external_404(monkeypatch):
    request = httpx.Request("GET", "https://example.test/word")
    response = httpx.Response(404, request=request)
    cause = httpx.HTTPStatusError("not found", request=request, response=response)

    def fake_get_json(url: str, **kwargs) -> None:
        raise _external_api_error_from(cause)

    monkeypatch.setattr("app.services.en_dictionary.get_json", fake_get_json)

    with pytest.raises(DictionaryLookupError):
        fetch_en_dictionary_data("qwertyzzz")


def test_fetch_raises_lookup_error_on_empty_array(monkeypatch):
    monkeypatch.setattr("app.services.en_dictionary.get_json", lambda url, **kwargs: [])

    with pytest.raises(DictionaryLookupError):
        fetch_en_dictionary_data("qwertyzzz")


def test_fetch_reraises_external_api_error_on_timeout(monkeypatch):
    cause = httpx.TimeoutException("timed out")

    def fake_get_json(url: str, **kwargs) -> None:
        raise _external_api_error_from(cause)

    monkeypatch.setattr("app.services.en_dictionary.get_json", fake_get_json)

    with pytest.raises(ExternalApiError):
        fetch_en_dictionary_data("hello")
