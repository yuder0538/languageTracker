def _media_log_payload(**overrides):
    base = {
        "language": "en",
        "title": "Friends",
        "media_type": "drama",
        "watched_date": "2026-01-01",
        "duration_minutes": 25,
    }
    base.update(overrides)
    return base


def _vocab_payload(**overrides):
    base = {"language": "en", "headword": "run", "ipa": "/rʌn/"}
    base.update(overrides)
    return base


def test_create_en_word_with_ipa(client):
    response = client.post("/api/v1/vocabulary", json=_vocab_payload())
    assert response.status_code == 201
    assert response.json()["ipa"] == "/rʌn/"


def test_create_de_word_with_artikel(client):
    response = client.post(
        "/api/v1/vocabulary",
        json=_vocab_payload(
            language="de", headword="Haus", ipa=None, de_artikel="das", de_plural="Häuser"
        ),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["de_artikel"] == "das"
    assert body["de_plural"] == "Häuser"


def test_create_en_word_rejects_de_artikel(client):
    response = client.post(
        "/api/v1/vocabulary",
        json=_vocab_payload(ipa=None, de_artikel="der"),
    )
    assert response.status_code == 422


def test_create_de_word_rejects_ipa(client):
    response = client.post(
        "/api/v1/vocabulary",
        json=_vocab_payload(language="de", headword="Haus", ipa="/haus/"),
    )
    assert response.status_code == 422


def test_list_requires_language_query_param(client):
    response = client.get("/api/v1/vocabulary")
    assert response.status_code == 422


def test_list_filters_by_language(client):
    client.post("/api/v1/vocabulary", json=_vocab_payload(language="en", headword="run"))
    client.post(
        "/api/v1/vocabulary",
        json=_vocab_payload(language="de", headword="laufen", ipa=None),
    )

    en_words = client.get("/api/v1/vocabulary", params={"language": "en"}).json()
    de_words = client.get("/api/v1/vocabulary", params={"language": "de"}).json()

    assert [w["headword"] for w in en_words] == ["run"]
    assert [w["headword"] for w in de_words] == ["laufen"]


def test_media_log_id_language_mismatch_rejected(client):
    media_log = client.post(
        "/api/v1/media-logs", json=_media_log_payload(language="en")
    ).json()

    response = client.post(
        "/api/v1/vocabulary",
        json=_vocab_payload(
            language="de", headword="laufen", ipa=None, media_log_id=media_log["id"]
        ),
    )
    assert response.status_code == 422


def test_media_log_id_language_match_accepted(client):
    media_log = client.post(
        "/api/v1/media-logs", json=_media_log_payload(language="en")
    ).json()

    response = client.post(
        "/api/v1/vocabulary",
        json=_vocab_payload(language="en", headword="run", media_log_id=media_log["id"]),
    )
    assert response.status_code == 201
    assert response.json()["media_log_id"] == media_log["id"]


def test_get_missing_vocabulary_returns_404(client):
    response = client.get("/api/v1/vocabulary/9999")
    assert response.status_code == 404


def test_patch_ignores_language_and_revalidates_specialized_fields(client):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload()).json()

    ok_response = client.patch(
        f"/api/v1/vocabulary/{created['id']}",
        json={"translation_zh": "跑", "language": "de"},
    )
    assert ok_response.status_code == 200
    body = ok_response.json()
    assert body["language"] == "en"
    assert body["translation_zh"] == "跑"

    bad_response = client.patch(
        f"/api/v1/vocabulary/{created['id']}",
        json={"de_artikel": "der"},
    )
    assert bad_response.status_code == 422


def test_delete_vocabulary(client):
    created = client.post("/api/v1/vocabulary", json=_vocab_payload()).json()

    delete_response = client.delete(f"/api/v1/vocabulary/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/vocabulary/{created['id']}")
    assert get_response.status_code == 404
