VALID_SRT = """1
00:00:01,000 --> 00:00:03,500
I love to run every morning.

2
00:00:04,000 --> 00:00:06,250
General Kenobi.
"""


def _create_media_log(client):
    payload = {
        "language": "en",
        "title": "Friends",
        "media_type": "drama",
        "watched_date": "2026-01-01",
        "duration_minutes": 25,
    }
    return client.post("/api/v1/media-logs", json=payload).json()


def _upload_subtitles(client, media_log_id, content: str = VALID_SRT):
    return client.post(
        f"/api/v1/media-logs/{media_log_id}/subtitles",
        files={"file": ("episode.srt", content.encode("utf-8"), "text/plain")},
    )


def _create_vocabulary(client, **overrides):
    base = {"language": "en", "headword": "run", "ipa": None}
    base.update(overrides)
    return client.post("/api/v1/vocabulary", json=base).json()


def test_enrich_fills_example_sentence_from_matching_subtitle_line(client):
    media_log = _create_media_log(client)
    _upload_subtitles(client, media_log["id"])
    vocab = _create_vocabulary(client, media_log_id=media_log["id"])

    response = client.post(f"/api/v1/vocabulary/{vocab['id']}/enrich/example-sentence")

    assert response.status_code == 200
    assert response.json()["example_sentence"] == "I love to run every morning."


def test_enrich_is_case_insensitive(client):
    media_log = _create_media_log(client)
    _upload_subtitles(client, media_log["id"])
    vocab = _create_vocabulary(client, headword="RUN", media_log_id=media_log["id"])

    response = client.post(f"/api/v1/vocabulary/{vocab['id']}/enrich/example-sentence")

    assert response.status_code == 200
    assert response.json()["example_sentence"] == "I love to run every morning."


def test_enrich_missing_vocabulary_returns_404(client):
    response = client.post("/api/v1/vocabulary/9999/enrich/example-sentence")
    assert response.status_code == 404


def test_enrich_without_media_log_returns_422(client):
    vocab = _create_vocabulary(client)

    response = client.post(f"/api/v1/vocabulary/{vocab['id']}/enrich/example-sentence")

    assert response.status_code == 422
    assert "未關聯劇集紀錄" in response.json()["detail"]


def test_enrich_without_uploaded_subtitles_returns_422(client):
    media_log = _create_media_log(client)
    vocab = _create_vocabulary(client, media_log_id=media_log["id"])

    response = client.post(f"/api/v1/vocabulary/{vocab['id']}/enrich/example-sentence")

    assert response.status_code == 422
    assert "尚未上傳字幕" in response.json()["detail"]


def test_enrich_word_not_found_in_subtitles_returns_404(client):
    media_log = _create_media_log(client)
    _upload_subtitles(client, media_log["id"])
    vocab = _create_vocabulary(client, headword="banana", media_log_id=media_log["id"])

    response = client.post(f"/api/v1/vocabulary/{vocab['id']}/enrich/example-sentence")

    assert response.status_code == 404
    assert "找不到此單字" in response.json()["detail"]
