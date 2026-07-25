HEADER = "language,title,media_type,watched_date,duration_minutes,notes"


def _upload(client, content: str, filename: str = "logs.csv"):
    return client.post(
        "/api/v1/media-logs/import-csv",
        files={"file": (filename, content.encode("utf-8"), "text/csv")},
    )


def _row(**overrides):
    base = {
        "language": "en",
        "title": "Friends",
        "media_type": "drama",
        "watched_date": "2026-01-01",
        "duration_minutes": "25",
        "notes": "",
    }
    base.update(overrides)
    return ",".join(base[col] for col in HEADER.split(","))


def test_import_creates_all_valid_rows(client):
    rows = [
        _row(title="Friends"),
        _row(title="Seinfeld", duration_minutes="22"),
    ]
    content = HEADER + "\n" + "\n".join(rows) + "\n"

    response = _upload(client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 2
    assert body["skipped"] == 0
    assert body["errors"] == []

    listed = client.get("/api/v1/media-logs", params={"language": "en"}).json()
    assert len(listed) == 2
    assert {item["title"] for item in listed} == {"Friends", "Seinfeld"}


def test_import_partial_success_records_row_errors(client):
    rows = [
        _row(title="Friends"),
        _row(title=""),  # invalid: title required
    ]
    content = HEADER + "\n" + "\n".join(rows) + "\n"

    response = _upload(client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 1
    assert body["skipped"] == 1
    assert body["errors"][0]["row"] == 3  # header=1, first row=2, second row=3
    assert "title" in body["errors"][0]["message"]

    listed = client.get("/api/v1/media-logs", params={"language": "en"}).json()
    assert len(listed) == 1


def test_import_rejects_non_csv_extension(client):
    content = HEADER + "\n" + _row(title="Friends") + "\n"

    response = _upload(client, content, filename="logs.txt")

    assert response.status_code == 422


def test_import_rejects_file_larger_than_limit(client):
    oversized_row = _row(title="Friends", notes="x" * (5 * 1024 * 1024 + 1))
    content = HEADER + "\n" + oversized_row + "\n"

    response = _upload(client, content)

    assert response.status_code == 422
    listed = client.get("/api/v1/media-logs", params={"language": "en"}).json()
    assert len(listed) == 0


def test_import_rejects_empty_file(client):
    response = _upload(client, "", filename="empty.csv")

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 0
    assert body["skipped"] == 0


def test_import_row_with_extra_columns_is_skipped_not_500(client):
    rows = [
        _row(title="Friends"),
        _row(title="Seinfeld") + ",unexpected_extra_value",
    ]
    content = HEADER + "\n" + "\n".join(rows) + "\n"

    response = _upload(client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 1
    assert body["skipped"] == 1
    assert body["errors"][0]["row"] == 3
    assert "欄位數" in body["errors"][0]["message"]

    listed = client.get("/api/v1/media-logs", params={"language": "en"}).json()
    assert len(listed) == 1


def test_export_escapes_formula_like_fields(client):
    client.post(
        "/api/v1/media-logs",
        json={
            "language": "en",
            "title": "=cmd|'/c calc'!A1",
            "media_type": "drama",
            "watched_date": "2026-01-01",
            "duration_minutes": 25,
            "notes": "@SUM(1,1)",
        },
    )

    response = client.get("/api/v1/media-logs/export-csv", params={"language": "en"})

    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert "'=cmd" in lines[1]
    assert "'@SUM" in lines[1]


def test_export_returns_csv_with_expected_headers(client):
    client.post(
        "/api/v1/media-logs",
        json={
            "language": "en",
            "title": "Friends",
            "media_type": "drama",
            "watched_date": "2026-01-01",
            "duration_minutes": 25,
        },
    )

    response = client.get("/api/v1/media-logs/export-csv", params={"language": "en"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "media_logs_export_en.csv" in response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    assert lines[0] == HEADER
    assert "Friends" in lines[1]


def test_export_requires_language_query_param(client):
    response = client.get("/api/v1/media-logs/export-csv")
    assert response.status_code == 422


def test_export_then_import_round_trip_preserves_content(client):
    client.post(
        "/api/v1/media-logs",
        json={
            "language": "en",
            "title": "Friends",
            "media_type": "drama",
            "watched_date": "2026-01-01",
            "duration_minutes": 25,
            "notes": "great show",
        },
    )
    client.post(
        "/api/v1/media-logs",
        json={
            "language": "en",
            "title": "Seinfeld",
            "media_type": "sitcom",
            "watched_date": "2026-02-15",
            "duration_minutes": 22,
        },
    )

    exported = client.get("/api/v1/media-logs/export-csv", params={"language": "en"})
    assert exported.status_code == 200

    import_response = _upload(client, exported.text, filename="roundtrip.csv")

    assert import_response.status_code == 200
    body = import_response.json()
    assert body["created"] == 2
    assert body["skipped"] == 0

    listed = client.get("/api/v1/media-logs", params={"language": "en"}).json()
    assert len(listed) == 4  # original 2 + re-imported 2 (each pair has identical field values)

    friends_entries = [item for item in listed if item["title"] == "Friends"]
    seinfeld_entries = [item for item in listed if item["title"] == "Seinfeld"]
    assert len(friends_entries) == 2
    assert len(seinfeld_entries) == 2
    for entry in friends_entries:
        assert entry["media_type"] == "drama"
        assert entry["watched_date"] == "2026-01-01"
        assert entry["duration_minutes"] == 25
        assert entry["notes"] == "great show"
    for entry in seinfeld_entries:
        assert entry["media_type"] == "sitcom"
        assert entry["watched_date"] == "2026-02-15"
        assert entry["duration_minutes"] == 22
