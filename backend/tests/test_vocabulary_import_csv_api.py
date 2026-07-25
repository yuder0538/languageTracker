HEADER = (
    "language,headword,part_of_speech,translation_zh,example_sentence,"
    "media_log_id,ipa,de_artikel,de_plural,de_conjugation,notes"
)


def _upload(client, content: str, filename: str = "words.csv"):
    return client.post(
        "/api/v1/vocabulary/import-csv",
        files={"file": (filename, content.encode("utf-8"), "text/csv")},
    )


def _row(**overrides):
    base = {
        "language": "en",
        "headword": "run",
        "part_of_speech": "",
        "translation_zh": "",
        "example_sentence": "",
        "media_log_id": "",
        "ipa": "",
        "de_artikel": "",
        "de_plural": "",
        "de_conjugation": "",
        "notes": "",
    }
    base.update(overrides)
    return ",".join(base[col] for col in HEADER.split(","))


def test_import_creates_all_valid_rows(client):
    rows = [
        _row(headword="run"),
        _row(headword="jump"),
        _row(headword="Haus", language="de", de_artikel="das"),
    ]
    content = HEADER + "\n" + "\n".join(rows) + "\n"

    response = _upload(client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 3
    assert body["skipped"] == 0
    assert body["errors"] == []

    en_listed = client.get("/api/v1/vocabulary", params={"language": "en"}).json()
    assert len(en_listed) == 2
    assert {item["headword"] for item in en_listed} == {"run", "jump"}

    de_listed = client.get("/api/v1/vocabulary", params={"language": "de"}).json()
    assert len(de_listed) == 1
    assert de_listed[0]["headword"] == "Haus"
    assert de_listed[0]["de_artikel"] == "das"


def test_import_partial_success_records_row_errors(client):
    rows = [
        _row(headword="run"),
        _row(headword="run", language="en", de_artikel="der"),  # invalid: en + de_artikel
    ]
    content = HEADER + "\n" + "\n".join(rows) + "\n"

    response = _upload(client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 1
    assert body["skipped"] == 1
    assert len(body["errors"]) == 1
    assert body["errors"][0]["row"] == 3  # header=1, first row=2, second row=3

    listed = client.get("/api/v1/vocabulary", params={"language": "en"}).json()
    assert len(listed) == 1


def test_import_skips_row_with_invalid_media_log_id(client):
    rows = [_row(headword="run", media_log_id="9999")]
    content = HEADER + "\n" + "\n".join(rows) + "\n"

    response = _upload(client, content)

    body = response.json()
    assert body["created"] == 0
    assert body["skipped"] == 1
    assert "media_log_id" in body["errors"][0]["message"]

    listed = client.get("/api/v1/vocabulary", params={"language": "en"}).json()
    assert listed == []


def test_import_skips_row_with_extra_columns_without_crashing(client):
    valid = _row(headword="run")
    extra_column_row = _row(headword="jump") + ",unexpected,extra"
    content = HEADER + "\n" + valid + "\n" + extra_column_row + "\n"

    response = _upload(client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 1
    assert body["skipped"] == 1
    assert body["errors"][0]["row"] == 3


def test_import_rejects_non_csv_extension(client):
    content = HEADER + "\n" + _row(headword="run") + "\n"

    response = _upload(client, content, filename="words.txt")

    assert response.status_code == 422


def test_import_rejects_file_larger_than_limit(client):
    oversized_row = _row(headword="run", notes="x" * (5 * 1024 * 1024 + 1))
    content = HEADER + "\n" + oversized_row + "\n"

    response = _upload(client, content)

    assert response.status_code == 422
