def _create_vocabulary(client, **overrides):
    base = {"language": "en", "headword": "run", "ipa": "/rʌn/"}
    base.update(overrides)
    return client.post("/api/v1/vocabulary", json=base).json()


def test_export_anki_returns_tsv_with_expected_headers(client):
    _create_vocabulary(client)

    response = client.get("/api/v1/vocabulary/export/anki", params={"language": "en"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/tab-separated-values")
    assert "anki_export_en.txt" in response.headers["content-disposition"]
    assert "run [/rʌn/]" in response.text


def test_export_anki_empty_language_returns_empty_body(client):
    response = client.get("/api/v1/vocabulary/export/anki", params={"language": "en"})

    assert response.status_code == 200
    assert response.text == ""


def test_export_anki_german_noun_includes_artikel_and_translation(client):
    _create_vocabulary(
        client,
        language="de",
        headword="Haus",
        ipa=None,
        de_artikel="das",
        translation_zh="房子",
    )

    response = client.get("/api/v1/vocabulary/export/anki", params={"language": "de"})

    lines = response.text.splitlines()
    assert len(lines) == 1
    front, back = lines[0].split("\t")
    assert front == "das Haus"
    assert back == "房子"


def test_export_anki_isolated_per_language(client):
    _create_vocabulary(client, language="en", headword="run", ipa=None)
    _create_vocabulary(client, language="de", headword="laufen", ipa=None)

    en_response = client.get("/api/v1/vocabulary/export/anki", params={"language": "en"})
    de_response = client.get("/api/v1/vocabulary/export/anki", params={"language": "de"})

    assert "run" in en_response.text
    assert "laufen" not in en_response.text
    assert "laufen" in de_response.text
    assert "run" not in de_response.text


def test_export_anki_requires_language_query_param(client):
    response = client.get("/api/v1/vocabulary/export/anki")
    assert response.status_code == 422
