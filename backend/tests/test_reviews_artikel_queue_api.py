import datetime as dt

from app.models.enums import DeArtikel
from app.models.vocabulary import Vocabulary


def _add_vocabulary(db_session, **overrides):
    base = {"language": "de", "headword": "word"}
    base.update(overrides)
    vocab = Vocabulary(**base)
    db_session.add(vocab)
    db_session.commit()
    db_session.refresh(vocab)
    return vocab


def test_artikel_queue_only_returns_nouns_with_de_artikel(client, db_session):
    noun = _add_vocabulary(db_session, headword="Haus", de_artikel=DeArtikel.DAS)
    _add_vocabulary(db_session, headword="laufen")  # verb, no de_artikel

    response = client.get(
        "/api/v1/reviews/queue", params={"language": "de", "card_type": "artikel"}
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [noun.id]


def test_artikel_queue_filters_due_cards_too(client, db_session):
    past = dt.datetime.utcnow() - dt.timedelta(days=1)
    noun = _add_vocabulary(
        db_session,
        headword="Haus",
        de_artikel=DeArtikel.DAS,
        srs_last_reviewed_at=past,
        srs_next_review_at=past,
    )
    _add_vocabulary(
        db_session,
        headword="laufen",
        srs_last_reviewed_at=past,
        srs_next_review_at=past,
    )  # due verb, no de_artikel

    response = client.get(
        "/api/v1/reviews/queue", params={"language": "de", "card_type": "artikel"}
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [noun.id]


def test_standard_queue_unaffected_by_artikel_cards(client, db_session):
    noun = _add_vocabulary(db_session, headword="Haus", de_artikel=DeArtikel.DAS)
    verb = _add_vocabulary(db_session, headword="laufen")

    response = client.get("/api/v1/reviews/queue", params={"language": "de"})

    ids = {item["id"] for item in response.json()}
    assert ids == {noun.id, verb.id}


def test_artikel_queue_rejects_english(client):
    response = client.get(
        "/api/v1/reviews/queue", params={"language": "en", "card_type": "artikel"}
    )

    assert response.status_code == 422
