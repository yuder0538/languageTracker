def _payload(**overrides):
    base = {
        "language": "en",
        "title": "Friends",
        "media_type": "drama",
        "watched_date": "2026-01-01",
        "duration_minutes": 25,
    }
    base.update(overrides)
    return base


def test_create_and_get_media_log(client):
    create_response = client.post("/api/v1/media-logs", json=_payload())
    assert create_response.status_code == 201
    media_log_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/media-logs/{media_log_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Friends"


def test_list_requires_language_query_param(client):
    response = client.get("/api/v1/media-logs")
    assert response.status_code == 422


def test_list_filters_by_language(client):
    client.post("/api/v1/media-logs", json=_payload(language="en", title="EN show"))
    client.post("/api/v1/media-logs", json=_payload(language="de", title="DE show"))

    en_response = client.get("/api/v1/media-logs", params={"language": "en"})
    de_response = client.get("/api/v1/media-logs", params={"language": "de"})

    assert [row["title"] for row in en_response.json()] == ["EN show"]
    assert [row["title"] for row in de_response.json()] == ["DE show"]


def test_get_missing_media_log_returns_404(client):
    response = client.get("/api/v1/media-logs/9999")
    assert response.status_code == 404


def test_create_rejects_negative_duration(client):
    response = client.post("/api/v1/media-logs", json=_payload(duration_minutes=-5))
    assert response.status_code == 422


def test_patch_updates_fields_but_ignores_language(client):
    create_response = client.post("/api/v1/media-logs", json=_payload(language="en"))
    media_log_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/v1/media-logs/{media_log_id}",
        json={"title": "Updated Title", "language": "de"},
    )
    assert patch_response.status_code == 200
    body = patch_response.json()
    assert body["title"] == "Updated Title"
    assert body["language"] == "en"


def test_delete_media_log(client):
    create_response = client.post("/api/v1/media-logs", json=_payload())
    media_log_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/media-logs/{media_log_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/media-logs/{media_log_id}")
    assert get_response.status_code == 404
