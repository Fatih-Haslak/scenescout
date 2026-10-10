"""SQLite metadata + float32 vectors; each operation owns its connection."""

import sqlite3
from contextlib import contextmanager

from .config import DATA_DIR


@contextmanager
def connection():
    with sqlite3.connect(DATA_DIR / "library.sqlite3", timeout=30) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        yield db


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
            """UPDATE videos SET status='error', error=?
                      WHERE status IN ('queued','indexing')""",
            ("Indexing was interrupted. Remove and import this video again.",),
        )


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
