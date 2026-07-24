from app.services.en_dictionary import DictionaryLookupError, EnDictionaryData
from app.services.http_client import ExternalApiError


def _vocab_payload(**overrides):
    base = {"language": "en", "headword": "run", "ipa": None}
    base.update(overrides)
    return base


def test_enrich_fills_ipa_and_definition(client, monkeypatch):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload()).json()

    monkeypatch.setattr(
        "app.api.vocabulary.fetch_en_dictionary_data",
        lambda headword: EnDictionaryData(
            ipa="/rʌn/", definition="to move fast", part_of_speech="verb"
        ),
    )

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/en-dictionary")

    assert response.status_code == 200
    body = response.json()
    assert body["ipa"] == "/rʌn/"
    assert body["en_definition"] == "to move fast"
    assert body["part_of_speech"] == "verb"


def test_enrich_does_not_overwrite_existing_part_of_speech(client, monkeypatch):
    created = client.post(
        "/api/v1/vocabulary", json=_vocab_payload(part_of_speech="noun")
    ).json()

    monkeypatch.setattr(
        "app.api.vocabulary.fetch_en_dictionary_data",
        lambda headword: EnDictionaryData(
            ipa="/rʌn/", definition="to move fast", part_of_speech="verb"
        ),
    )

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/en-dictionary")

    assert response.status_code == 200
    assert response.json()["part_of_speech"] == "noun"


def test_enrich_overwrites_existing_ipa_and_definition(client, monkeypatch):
    created = client.post(
        "/api/v1/vocabulary", json=_vocab_payload(ipa="/old/")
    ).json()

    monkeypatch.setattr(
        "app.api.vocabulary.fetch_en_dictionary_data",
        lambda headword: EnDictionaryData(
            ipa="/new/", definition="fresh definition", part_of_speech=None
        ),
    )

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/en-dictionary")

    assert response.status_code == 200
    body = response.json()
    assert body["ipa"] == "/new/"
    assert body["en_definition"] == "fresh definition"


def test_enrich_rejects_de_language(client):
    created = client.post(
        "/api/v1/vocabulary",
        json={"language": "de", "headword": "laufen"},
    ).json()

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/en-dictionary")

    assert response.status_code == 422


def test_enrich_missing_vocabulary_returns_404(client):
    response = client.post("/api/v1/vocabulary/9999/enrich/en-dictionary")
    assert response.status_code == 404


def test_enrich_returns_502_with_distinct_message_when_dictionary_has_no_entry(
    client, monkeypatch
):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload(headword="qwertyzzz")).json()

    def raise_lookup_error(headword: str):
        raise DictionaryLookupError(f"No dictionary entry found for '{headword}'")

    monkeypatch.setattr("app.api.vocabulary.fetch_en_dictionary_data", raise_lookup_error)

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/en-dictionary")

    assert response.status_code == 502
    assert "查無此字" in response.json()["detail"]


def test_enrich_returns_502_with_distinct_message_on_external_service_failure(
    client, monkeypatch
):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload()).json()

    def raise_external_error(headword: str):
        raise ExternalApiError("Request timed out")

    monkeypatch.setattr("app.api.vocabulary.fetch_en_dictionary_data", raise_external_error)

    response = client.post(f"/api/v1/vocabulary/{created['id']}/enrich/en-dictionary")

    assert response.status_code == 502
    assert "暫時無法連線" in response.json()["detail"]
