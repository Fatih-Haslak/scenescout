"""SQLite metadata + float32 vectors; each operation owns its connection."""

import sqlite3
import shutil
import threading
import logging
from contextlib import contextmanager

from .config import DATA_DIR

_generation = 0
_generation_lock = threading.Lock()
logger = logging.getLogger(__name__)


def invalidate():
    global _generation
    with _generation_lock:
        _generation += 1


def generation():
    with _generation_lock:
        return _generation


@contextmanager
def connection():
    db = sqlite3.connect(DATA_DIR / "library.sqlite3", timeout=30)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        with db:
            yield db
    finally:
        db.close()


def initialize():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "videos").mkdir(exist_ok=True)
    (DATA_DIR / "thumbnails").mkdir(exist_ok=True)
    with connection() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, extension TEXT NOT NULL,
                digest TEXT UNIQUE NOT NULL, size INTEGER NOT NULL,
                duration REAL DEFAULT 0, interval REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued', progress INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0, error TEXT, elapsed REAL DEFAULT 0,
                created TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS scenes (
                id TEXT PRIMARY KEY, video_id TEXT NOT NULL,
                timestamp REAL NOT NULL, vector BLOB NOT NULL,
                FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS scenes_video ON scenes(video_id);
        """)
        db.execute(
            """UPDATE videos SET status='paused', error=?
                      WHERE status IN ('queued','indexing')""",
            ("Indexing interrupted. Resume to continue from saved frames.",),
        )
    # A persisted tombstone makes interrupted removal recoverable, including file cleanup.
    for item in videos():
        if item["status"] == "removing":
            try:
                remove(item["id"])
            except OSError:
                logger.exception("Removal recovery blocked for %s", item["id"])
                update(item["id"], error="File is in use. Close its player and retry removal.")
    invalidate()


def videos():
    with connection() as db:
        return [dict(row) for row in db.execute("SELECT * FROM videos ORDER BY created DESC, id")]


def video(video_id):
    with connection() as db:
        row = db.execute("SELECT * FROM videos WHERE id=?", (video_id,)).fetchone()
        return dict(row) if row else None


def update(video_id, **fields):
    allowed = {"status", "progress", "total", "duration", "error", "elapsed"}
    if not fields or not fields.keys() <= allowed:
        raise ValueError("Invalid video update")
    with connection() as db:
        assignments = ", ".join(f"{key}=?" for key in fields)
        db.execute(f"UPDATE videos SET {assignments} WHERE id=?", (*fields.values(), video_id))
    if "status" in fields:
        invalidate()


def checkpoint(video_id, scenes):
    """Commit a batch and its progress together; retries reuse already committed scene IDs."""
    with connection() as db:
        db.executemany("INSERT OR REPLACE INTO scenes VALUES (?,?,?,?)", scenes)
        db.execute(
            "UPDATE videos SET progress=(SELECT COUNT(*) FROM scenes WHERE video_id=?) WHERE id=?",
            (video_id, video_id),
        )


def remove(video_id):
    item = video(video_id)
    if not item:
        return
    update(video_id, status="removing")
    # Delete metadata last. If file cleanup fails/crashes, the next startup retries it.
    (DATA_DIR / "videos" / f"{video_id}{item['extension']}").unlink(missing_ok=True)
    thumb_dir = DATA_DIR / "thumbnails" / video_id
    if thumb_dir.exists():
        shutil.rmtree(thumb_dir)
    with connection() as db:
        db.execute("DELETE FROM videos WHERE id=?", (video_id,))
    invalidate()
