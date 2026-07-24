import datetime as dt

import pytest

from app.models.review_log import ReviewLog
from app.models.vocabulary import Vocabulary


def _create_vocabulary(client, **overrides):
    base = {"language": "en", "headword": "run", "ipa": None}
    base.update(overrides)
    return client.post("/api/v1/vocabulary", json=base).json()


def test_review_new_vocabulary_initializes_schedule(client, db_session):
    vocab = _create_vocabulary(client)

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review", json={"grade": "good"}
    )

    assert response.status_code == 200

    db_session.expire_all()
    row = db_session.get(Vocabulary, vocab["id"])
    assert row.srs_interval_days == 1
    assert row.srs_repetitions == 1
    assert row.srs_ease_factor == pytest.approx(2.5)
    assert row.srs_last_reviewed_at is not None
    assert row.srs_next_review_at is not None
    assert row.srs_next_review_at - row.srs_last_reviewed_at == dt.timedelta(
        days=row.srs_interval_days
    )

    logs = db_session.query(ReviewLog).filter(ReviewLog.vocabulary_id == vocab["id"]).all()
    assert len(logs) == 1
    assert logs[0].grade == "good"
    assert logs[0].interval_days_after == 1


def test_review_again_resets_interval_and_increments_lapses(client, db_session):
    vocab = _create_vocabulary(client)
    client.post(f"/api/v1/vocabulary/{vocab['id']}/review", json={"grade": "good"})
    client.post(f"/api/v1/vocabulary/{vocab['id']}/review", json={"grade": "good"})

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review", json={"grade": "again"}
    )

    assert response.status_code == 200

    db_session.expire_all()
    row = db_session.get(Vocabulary, vocab["id"])
    assert row.srs_interval_days == 1
    assert row.srs_repetitions == 0
    assert row.srs_lapses == 1

    logs = db_session.query(ReviewLog).filter(ReviewLog.vocabulary_id == vocab["id"]).all()
    assert len(logs) == 3


def test_review_repeated_easy_grades_never_overflow_datetime(client, db_session):
    vocab = _create_vocabulary(client)

    for _ in range(30):
        response = client.post(
            f"/api/v1/vocabulary/{vocab['id']}/review", json={"grade": "easy"}
        )
        assert response.status_code == 200

    db_session.expire_all()
    row = db_session.get(Vocabulary, vocab["id"])
    assert row.srs_interval_days <= 365 * 100
    assert row.srs_next_review_at is not None


def test_review_missing_vocabulary_returns_404(client):
    response = client.post("/api/v1/vocabulary/9999/review", json={"grade": "good"})
    assert response.status_code == 404


def test_review_invalid_grade_returns_422(client):
    vocab = _create_vocabulary(client)

    response = client.post(
        f"/api/v1/vocabulary/{vocab['id']}/review", json={"grade": "excellent"}
    )

    assert response.status_code == 422
