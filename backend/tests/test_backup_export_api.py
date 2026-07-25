import os
import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def _make_settings(db_path):
    class _Settings:
        database_url = f"sqlite:///{db_path}"

    return _Settings()


def _seed_source_db(path, row_count=10):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE vocabulary (id INTEGER PRIMARY KEY, headword TEXT)")
    conn.executemany(
        "INSERT INTO vocabulary (headword) VALUES (?)",
        [(f"word{i}",) for i in range(row_count)],
    )
    conn.commit()
    conn.close()


def test_export_backup_produces_valid_downloadable_snapshot(tmp_path, monkeypatch):
    source_path = tmp_path / "source.db"
    _seed_source_db(source_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(source_path))

    client = TestClient(app)
    response = client.get("/api/v1/backup/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "attachment" in response.headers["content-disposition"]
    assert "immersion_tracker_backup_" in response.headers["content-disposition"]

    downloaded_path = tmp_path / "downloaded.db"
    downloaded_path.write_bytes(response.content)

    verify_conn = sqlite3.connect(downloaded_path)
    tables = {
        row[0]
        for row in verify_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    count = verify_conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
    verify_conn.close()

    assert "vocabulary" in tables
    assert count == 10


def test_export_backup_stays_consistent_during_concurrent_write(tmp_path, monkeypatch):
    source_path = tmp_path / "source.db"
    _seed_source_db(source_path, row_count=50)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(source_path))

    from app.api.backup import create_backup_file

    dest_path = tmp_path / "dest.db"
    already_wrote = {"done": False}

    def write_once_during_backup(status, remaining, total):
        if already_wrote["done"]:
            return
        already_wrote["done"] = True
        # Fail fast instead of retrying for SQLite's default 5s busy-timeout if the
        # backup connection briefly holds a read lock on this same file.
        writer = sqlite3.connect(source_path, timeout=0.1)
        try:
            writer.execute("INSERT INTO vocabulary (headword) VALUES ('mid-backup')")
            writer.commit()
        except sqlite3.OperationalError:
            pass  # lock contention is expected/acceptable; the point is dest stays valid
        finally:
            writer.close()

    create_backup_file(
        str(source_path), str(dest_path), pages=1, progress=write_once_during_backup
    )

    verify_conn = sqlite3.connect(dest_path)
    integrity = verify_conn.execute("PRAGMA integrity_check").fetchone()[0]
    count = verify_conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
    verify_conn.close()

    assert integrity == "ok"
    assert count >= 50


def test_export_backup_removes_temp_file_after_response(tmp_path, monkeypatch):
    source_path = tmp_path / "source.db"
    _seed_source_db(source_path, row_count=1)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(source_path))

    captured_tmp_path = {}
    from app.api import backup as backup_module

    original_create_backup_file = backup_module.create_backup_file

    def spy_create_backup_file(source, dest, *args, **kwargs):
        captured_tmp_path["path"] = dest
        return original_create_backup_file(source, dest, *args, **kwargs)

    monkeypatch.setattr(backup_module, "create_backup_file", spy_create_backup_file)

    client = TestClient(app)
    response = client.get("/api/v1/backup/export")

    assert response.status_code == 200
    assert not os.path.exists(captured_tmp_path["path"])


def test_export_backup_missing_source_db_returns_404(tmp_path, monkeypatch):
    missing_path = tmp_path / "does-not-exist.db"
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(missing_path))

    client = TestClient(app)
    response = client.get("/api/v1/backup/export")

    assert response.status_code == 404


def test_export_backup_cleans_up_temp_file_on_backup_failure(tmp_path, monkeypatch):
    source_path = tmp_path / "source.db"
    _seed_source_db(source_path, row_count=1)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(source_path))

    captured_tmp_path = {}
    from app.api import backup as backup_module

    def failing_create_backup_file(source, dest, *args, **kwargs):
        captured_tmp_path["path"] = dest
        raise sqlite3.OperationalError("simulated backup failure")

    monkeypatch.setattr(backup_module, "create_backup_file", failing_create_backup_file)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/backup/export")

    assert response.status_code == 500
    assert not os.path.exists(captured_tmp_path["path"])
