from app.services.de_translation import TranslationApiError
from app.services.http_client import ExternalApiError


def _vocab_payload(**overrides):
    base = {"language": "de", "headword": "laufen"}
    base.update(overrides)
    return base


def test_enrich_fills_translation_zh(client, monkeypatch):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload()).json()

    monkeypatch.setattr(
        "app.api.vocabulary.fetch_de_to_zh_translation", lambda headword: "跑步"
    )

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/de-translation")

    assert response.status_code == 200
    assert response.json()["translation_zh"] == "跑步"


def test_enrich_rejects_en_language(client):
    created = client.post(
        "/api/v1/vocabulary", json={"language": "en", "headword": "run"}
    ).json()

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/de-translation")

    assert response.status_code == 422


def test_enrich_missing_vocabulary_returns_404(client):
    response = client.post("/api/v1/vocabulary/9999/enrich/de-translation")
    assert response.status_code == 404


def test_enrich_returns_502_when_mymemory_reports_non_200_status(client, monkeypatch):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload()).json()

    def raise_translation_error(headword: str):
        raise TranslationApiError(f"MyMemory translation failed for '{headword}'")

    monkeypatch.setattr(
        "app.api.vocabulary.fetch_de_to_zh_translation", raise_translation_error
    )

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/de-translation")

    assert response.status_code == 502
    assert "翻譯服務回應異常" in response.json()["detail"]


def test_enrich_returns_502_on_external_service_failure(client, monkeypatch):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload()).json()

    def raise_external_error(headword: str):
        raise ExternalApiError("Request timed out")

    monkeypatch.setattr(
        "app.api.vocabulary.fetch_de_to_zh_translation", raise_external_error
    )

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/de-translation")

    assert response.status_code == 502
    assert "暫時無法連線" in response.json()["detail"]
