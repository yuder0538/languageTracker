import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, MediaLog, Vocabulary
from app.models.enums import DeArtikel, Language


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_media_log_defaults_media_type(session):
    log = MediaLog(
        language=Language.EN,
        title="Friends",
        watched_date=dt.date(2026, 1, 1),
        duration_minutes=25,
    )
    session.add(log)
    session.commit()

    assert log.media_type == "drama"
    assert log.language == Language.EN


def test_media_log_rejects_negative_duration(session):
    log = MediaLog(
        language=Language.EN,
        title="Friends",
        watched_date=dt.date(2026, 1, 1),
        duration_minutes=-5,
    )
    session.add(log)
    with pytest.raises(Exception):
        session.commit()


def test_vocabulary_language_isolation(session):
    en_word = Vocabulary(language=Language.EN, headword="run", ipa="/rʌn/")
    de_word = Vocabulary(
        language=Language.DE,
        headword="laufen",
        de_artikel=None,
        de_plural=None,
    )
    session.add_all([en_word, de_word])
    session.commit()

    en_rows = session.query(Vocabulary).filter_by(language=Language.EN).all()
    de_rows = session.query(Vocabulary).filter_by(language=Language.DE).all()

    assert [w.headword for w in en_rows] == ["run"]
    assert [w.headword for w in de_rows] == ["laufen"]


def test_vocabulary_de_artikel_enum(session):
    word = Vocabulary(
        language=Language.DE,
        headword="Haus",
        de_artikel=DeArtikel.DAS,
        de_plural="Häuser",
    )
    session.add(word)
    session.commit()

    fetched = session.query(Vocabulary).filter_by(headword="Haus").one()
    assert fetched.de_artikel == DeArtikel.DAS
