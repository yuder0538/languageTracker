import hashlib
import sqlite3

from fastapi.testclient import TestClient

from app.main import app


def _make_settings(db_path):
    class _Settings:
        database_url = f"sqlite:///{db_path}"

    return _Settings()


def _create_schema(conn):
    conn.execute("CREATE TABLE vocabulary (id INTEGER PRIMARY KEY, headword TEXT)")
    conn.execute("CREATE TABLE media_log (id INTEGER PRIMARY KEY, title TEXT)")
    conn.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
    conn.execute("INSERT INTO alembic_version (version_num) VALUES ('head')")


def _build_valid_backup_bytes(tmp_path, headword="restored-word"):
    path = tmp_path / "valid_backup_source.db"
    conn = sqlite3.connect(path)
    _create_schema(conn)
    conn.execute("INSERT INTO vocabulary (headword) VALUES (?)", (headword,))
    conn.commit()
    conn.close()
    return path.read_bytes()


def _seed_live_db(path, headword="old-word"):
    conn = sqlite3.connect(path)
    _create_schema(conn)
    conn.execute("INSERT INTO vocabulary (headword) VALUES (?)", (headword,))
    conn.commit()
    conn.close()


def _hash_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _restore(client, content: bytes, confirm="true", filename="backup.db"):
    params = {"confirm": confirm} if confirm is not None else {}
    return client.post(
        "/api/v1/backup/restore",
        params=params,
        files={"file": (filename, content, "application/octet-stream")},
    )


def test_restore_replaces_live_database_and_creates_safety_backup(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path, headword="old-word")
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))

    backup_bytes = _build_valid_backup_bytes(tmp_path, headword="new-word")

    client = TestClient(app)
    response = _restore(client, backup_bytes)

    assert response.status_code == 200
    body = response.json()
    assert body["restored"] is True

    conn = sqlite3.connect(live_path)
    headword = conn.execute("SELECT headword FROM vocabulary").fetchone()[0]
    conn.close()
    assert headword == "new-word"

    safety_backup_path = tmp_path / body["safety_backup_filename"]
    assert safety_backup_path.exists()
    safety_conn = sqlite3.connect(safety_backup_path)
    integrity = safety_conn.execute("PRAGMA integrity_check").fetchone()[0]
    old_headword = safety_conn.execute("SELECT headword FROM vocabulary").fetchone()[0]
    safety_conn.close()
    assert integrity == "ok"
    assert old_headword == "old-word"


def test_restore_rejects_non_sqlite_file(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))
    before_hash = _hash_file(live_path)

    client = TestClient(app)
    response = _restore(client, b"this is not a sqlite database at all")

    assert response.status_code == 422
    assert _hash_file(live_path) == before_hash


def test_restore_rejects_sqlite_file_missing_required_tables(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))
    before_hash = _hash_file(live_path)

    empty_db_path = tmp_path / "empty.db"
    sqlite3.connect(empty_db_path).close()
    content = empty_db_path.read_bytes()

    client = TestClient(app)
    response = _restore(client, content)

    assert response.status_code == 422
    assert _hash_file(live_path) == before_hash


def test_restore_without_confirm_true_does_nothing(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))
    before_hash = _hash_file(live_path)

    backup_bytes = _build_valid_backup_bytes(tmp_path, headword="should-not-appear")

    client = TestClient(app)
    response = _restore(client, backup_bytes, confirm=None)

    assert response.status_code == 422
    assert _hash_file(live_path) == before_hash


def test_restore_with_confirm_false_does_nothing(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))
    before_hash = _hash_file(live_path)

    backup_bytes = _build_valid_backup_bytes(tmp_path, headword="should-not-appear")

    client = TestClient(app)
    response = _restore(client, backup_bytes, confirm="false")

    assert response.status_code == 422
    assert _hash_file(live_path) == before_hash


def test_restore_without_confirm_never_reads_uploaded_file(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))

    from starlette.datastructures import UploadFile

    read_calls = {"count": 0}
    original_read = UploadFile.read

    async def spy_read(self, *args, **kwargs):
        read_calls["count"] += 1
        return await original_read(self, *args, **kwargs)

    monkeypatch.setattr(UploadFile, "read", spy_read)

    backup_bytes = _build_valid_backup_bytes(tmp_path)

    client = TestClient(app)
    response = _restore(client, backup_bytes, confirm=None)

    assert response.status_code == 422
    assert read_calls["count"] == 0


def test_restore_rejects_file_larger_than_limit(tmp_path, monkeypatch):
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))
    before_hash = _hash_file(live_path)

    oversized = b"SQLite format 3\x00" + b"x" * (50 * 1024 * 1024 + 1)

    client = TestClient(app)
    response = _restore(client, oversized)

    assert response.status_code == 422
    assert _hash_file(live_path) == before_hash


def test_restore_aborts_and_stays_contained_when_safety_backup_fails(tmp_path, monkeypatch):
    """The single most important safety property for this destructive endpoint:
    if the pre-restore safety backup itself fails, the live database must remain
    completely untouched and the DB engine must never be disposed (i.e. the
    destructive steps never begin)."""
    live_path = tmp_path / "live.db"
    _seed_live_db(live_path)
    monkeypatch.setattr("app.api.backup.get_settings", lambda: _make_settings(live_path))
    before_hash = _hash_file(live_path)

    from app.api import backup as backup_module

    def failing_create_backup_file(*args, **kwargs):
        raise sqlite3.OperationalError("simulated safety-backup failure")

    monkeypatch.setattr(backup_module, "create_backup_file", failing_create_backup_file)

    disposed = {"called": False}
    monkeypatch.setattr(
        backup_module.engine, "dispose", lambda *a, **kw: disposed.__setitem__("called", True)
    )

    backup_bytes = _build_valid_backup_bytes(tmp_path, headword="should-not-appear")

    client = TestClient(app, raise_server_exceptions=False)
    response = _restore(client, backup_bytes)

    assert response.status_code == 500
    assert disposed["called"] is False
    assert _hash_file(live_path) == before_hash
