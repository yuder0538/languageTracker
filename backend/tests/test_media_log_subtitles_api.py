VALID_SRT = """1
00:00:01,000 --> 00:00:03,500
Hello there.

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


def _upload(client, media_log_id, content: str, filename: str = "episode.srt"):
    return client.post(
        f"/api/v1/media-logs/{media_log_id}/subtitles",
        files={"file": (filename, content.encode("utf-8"), "text/plain")},
    )


def test_upload_parses_and_stores_subtitle_lines(client):
    media_log = _create_media_log(client)

    response = _upload(client, media_log["id"], VALID_SRT)

    assert response.status_code == 200
    assert response.json() == {"media_log_id": media_log["id"], "line_count": 2}

    listed = client.get(f"/api/v1/media-logs/{media_log['id']}/subtitles").json()
    assert [line["text"] for line in listed] == ["Hello there.", "General Kenobi."]
    assert [line["start_ms"] for line in listed] == [1000, 4000]


def test_reupload_replaces_previous_subtitle_lines(client):
    media_log = _create_media_log(client)
    _upload(client, media_log["id"], VALID_SRT)

    second_srt = "1\n00:00:00,000 --> 00:00:01,000\nOnly line.\n"
    response = _upload(client, media_log["id"], second_srt)

    assert response.status_code == 200
    assert response.json()["line_count"] == 1

    listed = client.get(f"/api/v1/media-logs/{media_log['id']}/subtitles").json()
    assert len(listed) == 1
    assert listed[0]["text"] == "Only line."


def test_upload_rejects_non_srt_extension(client):
    media_log = _create_media_log(client)

    response = _upload(client, media_log["id"], VALID_SRT, filename="episode.txt")

    assert response.status_code == 422


def test_upload_rejects_malformed_content(client):
    media_log = _create_media_log(client)

    response = _upload(client, media_log["id"], "just plain text, not srt at all")

    assert response.status_code == 422


def test_upload_handles_utf8_bom(client):
    media_log = _create_media_log(client)

    response = client.post(
        f"/api/v1/media-logs/{media_log['id']}/subtitles",
        files={
            "file": (
                "episode.srt",
                b"\xef\xbb\xbf" + VALID_SRT.encode("utf-8"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["line_count"] == 2


def test_upload_rejects_file_larger_than_limit(client):
    media_log = _create_media_log(client)

    oversized_srt = "1\n00:00:01,000 --> 00:00:03,000\n" + ("x" * (2 * 1024 * 1024 + 1)) + "\n"
    response = _upload(client, media_log["id"], oversized_srt)

    assert response.status_code == 422
    assert "過大" in response.json()["detail"]


def test_upload_rejects_non_utf8_content(client):
    media_log = _create_media_log(client)

    response = client.post(
        f"/api/v1/media-logs/{media_log['id']}/subtitles",
        files={"file": ("episode.srt", b"\xff\xfe\x00\xff invalid bytes", "text/plain")},
    )

    assert response.status_code == 422
    assert "UTF-8" in response.json()["detail"]


def test_get_subtitles_returns_lines_ordered_by_start_ms_regardless_of_upload_order(client):
    media_log = _create_media_log(client)
    out_of_order_srt = (
        "1\n00:00:05,000 --> 00:00:06,000\nSecond.\n\n"
        "2\n00:00:01,000 --> 00:00:02,000\nFirst.\n"
    )

    _upload(client, media_log["id"], out_of_order_srt)

    listed = client.get(f"/api/v1/media-logs/{media_log['id']}/subtitles").json()
    assert [line["text"] for line in listed] == ["First.", "Second."]


def test_upload_missing_media_log_returns_404(client):
    response = _upload(client, 9999, VALID_SRT)

    assert response.status_code == 404


def test_list_subtitles_missing_media_log_returns_404(client):
    response = client.get("/api/v1/media-logs/9999/subtitles")

    assert response.status_code == 404


def test_deleting_media_log_cascades_subtitle_lines(client):
    media_log = _create_media_log(client)
    _upload(client, media_log["id"], VALID_SRT)

    client.delete(f"/api/v1/media-logs/{media_log['id']}")

    response = client.get(f"/api/v1/media-logs/{media_log['id']}/subtitles")
    assert response.status_code == 404
