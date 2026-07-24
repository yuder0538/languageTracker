import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def temp_db_url(tmp_path, monkeypatch):
    db_path = tmp_path / "test_migration.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)

    from app.core.config import get_settings

    get_settings.cache_clear()
    yield db_path
    get_settings.cache_clear()


@pytest.fixture()
def alembic_config():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def test_upgrade_creates_tables_and_downgrade_removes_them(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"media_log", "vocabulary"}.issubset(tables)

    command.downgrade(alembic_config, "base")

    conn = sqlite3.connect(temp_db_url)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert "media_log" not in tables
    assert "vocabulary" not in tables


def test_vocabulary_media_log_id_set_null_on_delete(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        "INSERT INTO media_log (language, title, media_type, watched_date, duration_minutes) "
        "VALUES ('en', 'Friends', 'drama', '2026-01-01', 25)"
    )
    media_log_id = conn.execute("SELECT id FROM media_log").fetchone()[0]
    conn.execute(
        "INSERT INTO vocabulary (language, headword, media_log_id) VALUES ('en', 'run', ?)",
        (media_log_id,),
    )
    conn.commit()

    conn.execute("DELETE FROM media_log WHERE id = ?", (media_log_id,))
    conn.commit()

    remaining = conn.execute("SELECT headword, media_log_id FROM vocabulary").fetchone()
    conn.close()

    assert remaining == ("run", None)


def test_en_and_de_vocabulary_rows_are_independent(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    conn.execute("INSERT INTO vocabulary (language, headword, ipa) VALUES ('en', 'run', '/rʌn/')")
    conn.execute(
        "INSERT INTO vocabulary (language, headword, de_artikel, de_plural) "
        "VALUES ('de', 'Haus', 'das', 'Häuser')"
    )
    conn.commit()

    en_words = conn.execute("SELECT headword FROM vocabulary WHERE language = 'en'").fetchall()
    de_words = conn.execute("SELECT headword FROM vocabulary WHERE language = 'de'").fetchall()
    conn.close()

    assert en_words == [("run",)]
    assert de_words == [("Haus",)]
