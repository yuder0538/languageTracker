import datetime as dt

from app.models.enums import ReviewGrade
from app.models.review_log import ReviewLog
from app.models.vocabulary import Vocabulary


def _make_settings(limit: int):
    class _Settings:
        daily_new_card_limit = limit

    return _Settings()


def _add_vocabulary(db_session, **overrides):
    base = {"language": "en", "headword": "word"}
    base.update(overrides)
    vocab = Vocabulary(**base)
    db_session.add(vocab)
    db_session.commit()
    db_session.refresh(vocab)
    return vocab


def test_queue_returns_overdue_card(client, db_session):
    past = dt.datetime.now() - dt.timedelta(days=1)
    vocab = _add_vocabulary(
        db_session, headword="run", srs_last_reviewed_at=past, srs_next_review_at=past
    )

    response = client.get("/api/v1/reviews/queue", params={"language": "en"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [vocab.id]


def test_queue_excludes_card_not_yet_due(client, db_session):
    future = dt.datetime.now() + dt.timedelta(days=5)
    _add_vocabulary(
        db_session,
        headword="run",
        srs_last_reviewed_at=dt.datetime.now(),
        srs_next_review_at=future,
    )

    response = client.get("/api/v1/reviews/queue", params={"language": "en"})

    assert response.json() == []


def test_queue_returns_new_cards_ordered_by_id(client, db_session):
    first = _add_vocabulary(db_session, headword="apple")
    second = _add_vocabulary(db_session, headword="banana")

    response = client.get("/api/v1/reviews/queue", params={"language": "en"})

    assert [item["id"] for item in response.json()] == [first.id, second.id]


def test_queue_due_cards_ordered_most_overdue_first(client, db_session):
    now = dt.datetime.now()
    less_overdue = _add_vocabulary(
        db_session,
        headword="a",
        srs_last_reviewed_at=now,
        srs_next_review_at=now - dt.timedelta(hours=1),
    )
    more_overdue = _add_vocabulary(
        db_session,
        headword="b",
        srs_last_reviewed_at=now,
        srs_next_review_at=now - dt.timedelta(days=3),
    )

    response = client.get("/api/v1/reviews/queue", params={"language": "en"})

    assert [item["id"] for item in response.json()] == [more_overdue.id, less_overdue.id]


def test_new_cards_capped_by_daily_limit(client, db_session, monkeypatch):
    monkeypatch.setattr("app.api.reviews.get_settings", lambda: _make_settings(2))
    for i in range(5):
        _add_vocabulary(db_session, headword=f"word{i}")

    response = client.get("/api/v1/reviews/queue", params={"language": "en"})

    assert len(response.json()) == 2


def test_new_cards_already_introduced_today_count_against_limit(
    client, db_session, monkeypatch
):
    monkeypatch.setattr("app.api.reviews.get_settings", lambda: _make_settings(2))

    already_seen = _add_vocabulary(
        db_session, headword="seen", srs_last_reviewed_at=dt.datetime.now()
    )
    db_session.add(
        ReviewLog(
            vocabulary_id=already_seen.id,
            reviewed_at=dt.datetime.now(),
            grade=ReviewGrade.GOOD,
            interval_days_after=1,
        )
    )
    db_session.commit()

    for i in range(3):
        _add_vocabulary(db_session, headword=f"fresh{i}")

    response = client.get("/api/v1/reviews/queue", params={"language": "en"})

    # already_seen has srs_last_reviewed_at but no srs_next_review_at, so it
    # falls into neither the due-cards nor new-cards segment and never appears
    # in the response; its review_log entry only counts against today's limit.
    returned_ids = {item["id"] for item in response.json()}
    assert already_seen.id not in returned_ids
    assert len(returned_ids) == 1


def test_queue_is_isolated_per_language(client, db_session):
    en_vocab = _add_vocabulary(db_session, language="en", headword="run")
    _add_vocabulary(db_session, language="de", headword="laufen")

    response = client.get("/api/v1/reviews/queue", params={"language": "en"})

    assert [item["id"] for item in response.json()] == [en_vocab.id]


def test_queue_requires_language_query_param(client):
    response = client.get("/api/v1/reviews/queue")
    assert response.status_code == 422
