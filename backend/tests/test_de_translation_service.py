import pytest

from app.services.de_translation import TranslationApiError, fetch_de_to_zh_translation
from app.services.http_client import ExternalApiError


def test_fetch_returns_translated_text(monkeypatch):
    def fake_get_json(url: str, params=None, **kwargs):
        assert params == {"q": "laufen", "langpair": "de|zh"}
        return {
            "responseData": {"translatedText": "跑步"},
            "responseStatus": 200,
        }

    monkeypatch.setattr("app.services.de_translation.get_json", fake_get_json)

    result = fetch_de_to_zh_translation("laufen")

    assert result == "跑步"


def test_fetch_returns_translated_text_when_response_status_is_string(monkeypatch):
    def fake_get_json(url: str, params=None, **kwargs):
        return {
            "responseData": {"translatedText": "跑步"},
            "responseStatus": "200",
        }

    monkeypatch.setattr("app.services.de_translation.get_json", fake_get_json)

    result = fetch_de_to_zh_translation("laufen")

    assert result == "跑步"


def test_fetch_raises_translation_api_error_on_malformed_response_data(monkeypatch):
    def fake_get_json(url: str, params=None, **kwargs):
        return {"responseStatus": 200}

    monkeypatch.setattr("app.services.de_translation.get_json", fake_get_json)

    with pytest.raises(TranslationApiError):
        fetch_de_to_zh_translation("laufen")


def test_fetch_raises_translation_api_error_on_non_200_response_status(monkeypatch):
    def fake_get_json(url: str, params=None, **kwargs):
        return {"responseData": {"translatedText": ""}, "responseStatus": 403}

    monkeypatch.setattr("app.services.de_translation.get_json", fake_get_json)

    with pytest.raises(TranslationApiError):
        fetch_de_to_zh_translation("laufen")


def test_fetch_reraises_external_api_error_on_timeout(monkeypatch):
    def fake_get_json(url: str, params=None, **kwargs):
        raise ExternalApiError("Request timed out")

    monkeypatch.setattr("app.services.de_translation.get_json", fake_get_json)

    with pytest.raises(ExternalApiError):
        fetch_de_to_zh_translation("laufen")
