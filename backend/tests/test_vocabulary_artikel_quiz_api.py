from app.models.vocabulary import Vocabulary


def _create_vocabulary(client, **overrides):
    base = {"language": "de", "headword": "Haus", "de_artikel": "das"}
    base.update(overrides)
    return client.post("/api/v1/vocabulary", json=base).json()


def test_correct_answer_marks_correct_and_advances_schedule(client, db_session):
    vocab = _create_vocabulary(client)

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review/artikel-quiz",
        json={"answer": "das"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"correct": True, "correct_answer": "das"}

    db_session.expire_all()
    row = db_session.get(Vocabulary, vocab["id"])
    assert row.srs_repetitions == 1
    assert row.srs_lapses == 0


def test_wrong_answer_marks_incorrect_and_resets_schedule(client, db_session):
    vocab = _create_vocabulary(client)

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review/artikel-quiz",
        json={"answer": "der"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"correct": False, "correct_answer": "das"}

    db_session.expire_all()
    row = db_session.get(Vocabulary, vocab["id"])
    assert row.srs_lapses == 1


def test_rejects_english_vocabulary(client):
    vocab = client.post(
        "/api/v1/vocabulary", json={"language": "en", "headword": "run"}
    ).json()

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review/artikel-quiz",
        json={"answer": "der"},
    )

    assert response.status_code == 422


def test_rejects_de_vocabulary_without_artikel(client):
    vocab = client.post(
        "/api/v1/vocabulary", json={"language": "de", "headword": "laufen"}
    ).json()

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review/artikel-quiz",
        json={"answer": "der"},
    )

    assert response.status_code == 422


def test_missing_vocabulary_returns_404(client):
    response = client.post(
        "/api/v1/vocabulary/9999/review/artikel-quiz", json={"answer": "der"}
    )
    assert response.status_code == 404


def test_invalid_answer_returns_422(client):
    vocab = _create_vocabulary(client)

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review/artikel-quiz",
        json={"answer": "le"},
    )

    assert response.status_code == 422
