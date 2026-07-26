import datetime as dt

from app.models.enums import ReviewGrade
from app.models.review_log import ReviewLog
from app.models.vocabulary import Vocabulary


def _add_vocabulary(db_session, **overrides):
    base = {"language": "en", "headword": "word"}
    base.update(overrides)
    vocab = Vocabulary(**base)
    db_session.add(vocab)
    db_session.commit()
    db_session.refresh(vocab)
    return vocab


def _add_review_log(db_session, vocabulary_id, reviewed_at, grade):
    db_session.add(
        ReviewLog(
            vocabulary_id=vocabulary_id,
            reviewed_at=reviewed_at,
            grade=grade,
            interval_days_after=1,
        )
    )
    db_session.commit()


def test_stats_reviewed_today_and_accuracy(client, db_session):
    vocab = _add_vocabulary(db_session)
    now = dt.datetime.now()
    _add_review_log(db_session, vocab.id, now, ReviewGrade.GOOD)
    _add_review_log(db_session, vocab.id, now, ReviewGrade.EASY)
    _add_review_log(db_session, vocab.id, now, ReviewGrade.AGAIN)

    response = client.get("/api/v1/reviews/stats", params={"language": "en"})

    assert response.status_code == 200
    body = response.json()
    assert body["reviewed_today"] == 3
    assert body["accuracy_today"] == 2 / 3


def test_stats_no_reviews_today_returns_null_accuracy(client, db_session):
    response = client.get("/api/v1/reviews/stats", params={"language": "en"})

    assert response.status_code == 200
    body = response.json()
    assert body["reviewed_today"] == 0
    assert body["accuracy_today"] is None


def test_stats_streak_counts_consecutive_days_with_gap(client, db_session):
    vocab = _add_vocabulary(db_session)
    today = dt.datetime.now()
    _add_review_log(db_session, vocab.id, today, ReviewGrade.GOOD)
    _add_review_log(db_session, vocab.id, today - dt.timedelta(days=1), ReviewGrade.GOOD)
    _add_review_log(db_session, vocab.id, today - dt.timedelta(days=2), ReviewGrade.GOOD)
    # gap: no review 3 days ago
    _add_review_log(db_session, vocab.id, today - dt.timedelta(days=4), ReviewGrade.GOOD)

    response = client.get("/api/v1/reviews/stats", params={"language": "en"})

    assert response.json()["streak_days"] == 3


def test_stats_streak_not_reset_when_today_has_no_review_yet(client, db_session):
    vocab = _add_vocabulary(db_session)
    yesterday = dt.datetime.now() - dt.timedelta(days=1)
    _add_review_log(db_session, vocab.id, yesterday, ReviewGrade.GOOD)
    _add_review_log(
        db_session, vocab.id, yesterday - dt.timedelta(days=1), ReviewGrade.GOOD
    )

    response = client.get("/api/v1/reviews/stats", params={"language": "en"})

    assert response.json()["streak_days"] == 2


def test_stats_isolated_per_language(client, db_session):
    en_vocab = _add_vocabulary(db_session, language="en")
    de_vocab = _add_vocabulary(db_session, language="de")
    now = dt.datetime.now()
    _add_review_log(db_session, en_vocab.id, now, ReviewGrade.GOOD)
    _add_review_log(db_session, de_vocab.id, now, ReviewGrade.AGAIN)
    _add_review_log(db_session, de_vocab.id, now, ReviewGrade.AGAIN)

    en_response = client.get("/api/v1/reviews/stats", params={"language": "en"})
    de_response = client.get("/api/v1/reviews/stats", params={"language": "de"})

    assert en_response.json() == {
        "reviewed_today": 1,
        "accuracy_today": 1.0,
        "streak_days": 1,
    }
    assert de_response.json() == {
        "reviewed_today": 2,
        "accuracy_today": 0.0,
        "streak_days": 1,
    }


def test_stats_requires_language_query_param(client):
    response = client.get("/api/v1/reviews/stats")
    assert response.status_code == 422
