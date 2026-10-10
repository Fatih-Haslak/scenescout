import sqlite3

import pytest

from scenescout import store


def test_connection_closes_after_success_and_failure(library):
    with store.connection() as db:
        db.execute("CREATE TABLE example (value INTEGER)")
    with pytest.raises(sqlite3.ProgrammingError):
        db.execute("SELECT 1")
    with pytest.raises(RuntimeError):
        with store.connection() as failed:
            failed.execute("INSERT INTO example VALUES (1)")
            raise RuntimeError("abort")
    with pytest.raises(sqlite3.ProgrammingError):
        failed.execute("SELECT 1")
    with store.connection() as check:
        assert check.execute("SELECT COUNT(*) FROM example").fetchone()[0] == 0


def test_checkpoint_atomic_and_retry_idempotent(add_video, vector):
    add_video()
    scene = ("a-00000", "a", 0, vector.tobytes())
    store.checkpoint("a", [scene])
    store.checkpoint("a", [scene])
    assert store.video("a")["progress"] == 1
    with pytest.raises(sqlite3.IntegrityError):
        store.checkpoint(
            "a", [("a-00001", "a", 3, vector.tobytes()), ("bad", "missing", 0, vector.tobytes())]
        )
    assert store.video("a")["progress"] == 1
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM scenes").fetchone()[0] == 1


def test_restart_recovers_interrupted_jobs_and_removal(add_video, library, vector):
    for status in ["queued", "indexing", "removing", "ready"]:
        add_video(status, status)
    store.checkpoint("removing", [("removed-frame", "removing", 0, vector.tobytes())])
    (library / "videos/removing.mp4").write_bytes(b"copy")
    thumb_dir = library / "thumbnails/removing"
    thumb_dir.mkdir()
    (thumb_dir / "removed-frame.jpg").write_bytes(b"thumbnail")
    store.initialize()
    assert store.video("queued")["status"] == "paused"
    assert store.video("indexing")["status"] == "paused"
    assert store.video("ready")["status"] == "ready"
    assert store.video("removing") is None
    assert not thumb_dir.exists()
    assert not (library / "videos/removing.mp4").exists()
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM scenes").fetchone()[0] == 0


def test_failed_cleanup_keeps_tombstone_for_retry(add_video, library, monkeypatch):
    add_video()
    (library / "thumbnails/a").mkdir()
    original = store.shutil.rmtree

    def fail(path):
        raise PermissionError("file in use")

    monkeypatch.setattr(store.shutil, "rmtree", fail)
    with pytest.raises(PermissionError):
        store.remove("a")
    assert store.video("a")["status"] == "removing"
    monkeypatch.setattr(store.shutil, "rmtree", original)
    store.initialize()
    assert store.video("a") is None


def test_one_locked_removal_does_not_prevent_startup(add_video, library, monkeypatch):
    add_video("a", "removing")
    add_video("b", "ready")
    (library / "thumbnails/a").mkdir()

    def fail(path):
        raise PermissionError("locked")

    monkeypatch.setattr(store.shutil, "rmtree", fail)
    store.initialize()
    assert store.video("a")["status"] == "removing"
    assert "retry removal" in store.video("a")["error"]
    assert store.video("b")["status"] == "ready"
