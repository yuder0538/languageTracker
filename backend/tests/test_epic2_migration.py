import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def temp_db_url(tmp_path, monkeypatch):
    db_path = tmp_path / "test_epic2_migration.db"
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


def test_upgrade_adds_en_definition_and_subtitle_line(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(vocabulary)")}
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    assert "en_definition" in columns
    assert "subtitle_line" in tables


def test_downgrade_one_step_removes_epic2_changes(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "d2f0916462fe")
    command.downgrade(alembic_config, "-1")

    conn = sqlite3.connect(temp_db_url)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(vocabulary)")}
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    assert "en_definition" not in columns
    assert "subtitle_line" not in tables

    command.upgrade(alembic_config, "head")


def test_subtitle_line_cascade_delete_on_media_log_removal(temp_db_url, alembic_config):
    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(temp_db_url)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        "INSERT INTO media_log (language, title, media_type, watched_date, duration_minutes) "
        "VALUES ('en', 'Friends', 'drama', '2026-01-01', 25)"
    )
    media_log_id = conn.execute("SELECT id FROM media_log").fetchone()[0]
    conn.execute(
        "INSERT INTO subtitle_line (media_log_id, start_ms, end_ms, text) "
        "VALUES (?, 0, 1000, 'Hi there')",
        (media_log_id,),
    )
    conn.commit()

    conn.execute("DELETE FROM media_log WHERE id = ?", (media_log_id,))
    conn.commit()

    remaining = conn.execute("SELECT COUNT(*) FROM subtitle_line").fetchone()[0]
    conn.close()

    assert remaining == 0
