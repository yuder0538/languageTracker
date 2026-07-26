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


def test_history_default_35_days_includes_zero_count_days(client, db_session):
    vocab = _add_vocabulary(db_session)
    _add_review_log(db_session, vocab.id, dt.datetime.now(), ReviewGrade.GOOD)

    response = client.get("/api/v1/reviews/history", params={"language": "en"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 35
    assert body[-1]["reviewed_count"] == 1
    assert body[0]["reviewed_count"] == 0


def test_history_respects_days_param(client, db_session):
    response = client.get(
        "/api/v1/reviews/history", params={"language": "en", "days": 7}
    )

    assert response.status_code == 200
    assert len(response.json()) == 7


def test_history_oldest_first_ending_today(client, db_session):
    today = dt.date.today()

    response = client.get(
        "/api/v1/reviews/history", params={"language": "en", "days": 7}
    )

    body = response.json()
    assert body[0]["date"] == (today - dt.timedelta(days=6)).isoformat()
    assert body[-1]["date"] == today.isoformat()


def test_history_counts_and_correct_count_per_day(client, db_session):
    vocab = _add_vocabulary(db_session)
    now = dt.datetime.now()
    _add_review_log(db_session, vocab.id, now, ReviewGrade.GOOD)
    _add_review_log(db_session, vocab.id, now, ReviewGrade.EASY)
    _add_review_log(db_session, vocab.id, now, ReviewGrade.AGAIN)

    response = client.get(
        "/api/v1/reviews/history", params={"language": "en", "days": 1}
    )

    today_entry = response.json()[-1]
    assert today_entry["reviewed_count"] == 3
    assert today_entry["correct_count"] == 2


def test_history_isolated_per_language(client, db_session):
    en_vocab = _add_vocabulary(db_session, language="en")
    de_vocab = _add_vocabulary(db_session, language="de")
    now = dt.datetime.now()
    _add_review_log(db_session, en_vocab.id, now, ReviewGrade.GOOD)
    _add_review_log(db_session, de_vocab.id, now, ReviewGrade.AGAIN)
    _add_review_log(db_session, de_vocab.id, now, ReviewGrade.AGAIN)

    en_today = client.get(
        "/api/v1/reviews/history", params={"language": "en", "days": 1}
    ).json()[-1]
    de_today = client.get(
        "/api/v1/reviews/history", params={"language": "de", "days": 1}
    ).json()[-1]

    assert en_today == {
        "date": dt.date.today().isoformat(),
        "reviewed_count": 1,
        "correct_count": 1,
    }
    assert de_today == {
        "date": dt.date.today().isoformat(),
        "reviewed_count": 2,
        "correct_count": 0,
    }


def test_history_requires_language_query_param(client):
    response = client.get("/api/v1/reviews/history")
    assert response.status_code == 422


def test_history_days_out_of_range_returns_422(client):
    too_few = client.get(
        "/api/v1/reviews/history", params={"language": "en", "days": 0}
    )
    too_many = client.get(
        "/api/v1/reviews/history", params={"language": "en", "days": 91}
    )

    assert too_few.status_code == 422
    assert too_many.status_code == 422
