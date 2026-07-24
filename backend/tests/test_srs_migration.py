import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def temp_db_url(tmp_path, monkeypatch):
    db_path = tmp_path / "test_srs_migration.db"
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


def test_upgrade_adds_srs_fields_and_review_log(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(vocabulary)")}
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    assert {
        "srs_interval_days",
        "srs_ease_factor",
        "srs_repetitions",
        "srs_lapses",
        "srs_next_review_at",
        "srs_last_reviewed_at",
    }.issubset(columns)
    assert "review_log" in tables


def test_downgrade_one_step_removes_srs_changes(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "3bdbced4ba98")
    command.downgrade(alembic_config, "-1")

    conn = sqlite3.connect(temp_db_url)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(vocabulary)")}
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    assert "srs_interval_days" not in columns
    assert "review_log" not in tables

    command.upgrade(alembic_config, "head")


def test_upgrade_backfills_existing_rows_with_default_srs_values(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "d2f0916462fe")

    conn = sqlite3.connect(temp_db_url)
    conn.execute("INSERT INTO vocabulary (language, headword) VALUES ('en', 'run')")
    conn.commit()
    conn.close()

    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    row = conn.execute(
        "SELECT srs_interval_days, srs_ease_factor, srs_repetitions, srs_lapses "
        "FROM vocabulary"
    ).fetchone()
    conn.close()

    assert row == (0, 2.5, 0, 0)


def test_new_vocabulary_rows_default_srs_fields(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    conn.execute(
        "INSERT INTO vocabulary (language, headword) VALUES ('en', 'run')"
    )
    conn.commit()
    row = conn.execute(
        "SELECT srs_interval_days, srs_ease_factor, srs_repetitions, srs_lapses "
        "FROM vocabulary"
    ).fetchone()
    conn.close()

    assert row == (0, 2.5, 0, 0)


def test_review_log_cascade_delete_on_vocabulary_removal(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("INSERT INTO vocabulary (language, headword) VALUES ('en', 'run')")
    vocabulary_id = conn.execute("SELECT id FROM vocabulary").fetchone()[0]
    conn.execute(
        "INSERT INTO review_log (vocabulary_id, grade, interval_days_after) "
        "VALUES (?, 'good', 1)",
        (vocabulary_id,),
    )
    conn.commit()

    conn.execute("DELETE FROM vocabulary WHERE id = ?", (vocabulary_id,))
    conn.commit()

    remaining = conn.execute("SELECT COUNT(*) FROM review_log").fetchone()[0]
    conn.close()

    assert remaining == 0
