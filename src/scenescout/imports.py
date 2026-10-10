"""Persistent, cancellable link imports, converted to local H.264 before indexing."""

import hashlib
import json
import logging
import math
import os
import re
import signal
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlsplit

import cv2
import imageio_ffmpeg

from . import store
from .config import DATA_DIR, MAX_DURATION_SECONDS, MAX_FRAMES, MAX_UPLOAD_BYTES
from .indexer import indexer

logger = logging.getLogger(__name__)
ACTIVE = {"queued", "downloading", "converting"}


def canonical_url(value):
    """Accept single public-platform video addresses; never a generic URL/network fetch."""
    try:
        parsed = urlsplit(value.strip())
        if (
            parsed.scheme != "https"
            or parsed.username
            or parsed.password
            or parsed.port not in {None, 443}
        ):
            raise ValueError
        host = parsed.hostname
        if host in {"youtu.be", "www.youtu.be"}:
            video_id = parsed.path.removeprefix("/")
        elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            if parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]
            else:
                matched = re.fullmatch(r"/(?:shorts|live)/([\w-]{11})/?", parsed.path)
                video_id = matched[1] if matched else ""
        elif host in {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}:
            matched = re.fullmatch(
                r"/([A-Za-z0-9_]{1,30}|i/web)/status/([0-9]{1,25})(?:/video/([0-9]+))?/?",
                parsed.path,
            )
            if matched:
                return f"https://x.com/{matched[1]}/status/{matched[2]}" + (
                    f"/video/{matched[3]}" if matched[3] else ""
                )
            raise ValueError
        else:
            raise ValueError
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            raise ValueError
        return f"https://www.youtube.com/watch?v={video_id}"
    except ValueError as exc:
        raise ValueError("Paste an HTTPS YouTube video/Shorts or X/Twitter post link.") from exc


def jobs():
    with store.connection() as db:
        return [
            dict(row)
            for row in db.execute("SELECT * FROM imports ORDER BY created DESC,id DESC LIMIT 20")
        ]


def job(job_id):
    with store.connection() as db:
        row = db.execute("SELECT * FROM imports WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def update(job_id, **fields):
    if not fields or not fields.keys() <= {"status", "downloaded", "title", "video_id", "error"}:
        raise ValueError("Invalid import update")
    with store.connection() as db:
        assignments = ",".join(f"{name}=?" for name in fields)
        db.execute(f"UPDATE imports SET {assignments} WHERE id=?", (*fields.values(), job_id))


def cleanup(job_id, delete=False):
    folder = DATA_DIR / "imports" / job_id
    if folder.exists():
        shutil.rmtree(folder)
    if delete:
        with store.connection() as db:
            db.execute("DELETE FROM imports WHERE id=?", (job_id,))


def initialize():
    (DATA_DIR / "imports").mkdir(exist_ok=True)
    with store.connection() as db:
        items = [dict(row) for row in db.execute("SELECT * FROM imports")]
    for item in items:
        try:
            cleanup(item["id"], delete=item["status"] == "removing")
        except OSError:
            logger.exception("Link import cleanup blocked")


def publish(path, title, url, interval):
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    video_id = uuid.uuid4().hex
    target = DATA_DIR / "videos" / f"{video_id}.mp4"
    try:
        with store.connection() as db:
            existing = db.execute("SELECT id FROM videos WHERE digest=?", (digest,)).fetchone()
            if existing:
                return existing["id"]
            path.replace(target)
            db.execute(
                "INSERT INTO videos(id,name,extension,digest,size,interval,source_url) VALUES(?,?,?,?,?,?,?)",
                (video_id, title, ".mp4", digest, target.stat().st_size, interval, url),
            )
        store.invalidate()
        indexer.submit(video_id)
        return video_id
    except Exception:
        # A committed video remains retryable even if submitting its index fails.
        if not store.video(video_id):
            target.unlink(missing_ok=True)
        raise


class Interrupted(Exception):
    pass


def run_process(command, folder, event, timeout, progress=None):
    """Own the child and stop it promptly on cancel/shutdown; no shell or platform logs in UI."""
    options = (
        {"creationflags": subprocess.CREATE_NO_WINDOW}
        if sys.platform == "win32"
        else {"start_new_session": True}
    )
    with (folder / "process.log").open("wb") as log:
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=log, stderr=log, **options
        )
        started = time.monotonic()
        try:
            while process.poll() is None:
                if event.wait(0.2):
                    raise Interrupted
                if time.monotonic() - started > timeout:
                    raise ValueError("Import timed out. Try a shorter video or upload its file.")
                if progress:
                    progress()
            if event.is_set():
                raise Interrupted
            return process.returncode
        finally:
            if process.poll() is None:
                # yt-dlp may own an ffmpeg child; stop the entire owned Windows process tree.
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        **options,
                    )
                else:
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def fetch_video(item, folder, event):
    last_bytes = -1

    def progress():
        nonlocal last_bytes
        if sum(p.stat().st_size for p in folder.glob("source.*") if p.is_file()) > MAX_UPLOAD_BYTES:
            raise ValueError("Video exceeds the 512 MB download limit.")
        try:
            count = json.loads((folder / "progress.json").read_text(encoding="utf-8"))["downloaded"]
        except (OSError, ValueError, KeyError):
            return
        if count != last_bytes:
            update(item["id"], downloaded=count)
            last_bytes = count

    code = run_process(
        [
            sys.executable,
            "-m",
            "scenescout.link_download",
            item["url"],
            str(folder),
            str(item["interval"]),
        ],
        folder,
        event,
        900,
        progress,
    )
    if code:
        error_file = folder / "error.json"
        if error_file.exists():
            error = json.loads(error_file.read_text(encoding="utf-8"))
            logger.warning("Link downloader failed (%s)", error.get("error_type", "unknown"))
            message = error["error"]
        else:
            message = "Download failed. Check the link and your internet connection."
        raise ValueError(message)
    result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    # The subprocess writes a basename, never a user-supplied file path.
    source = folder / result["file"]
    if source.parent != folder or not source.is_file():
        raise ValueError("Download did not produce a video.")
    if source.stat().st_size > MAX_UPLOAD_BYTES:
        raise ValueError("Video exceeds the 512 MB download limit.")
    cap = cv2.VideoCapture(str(source))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = count / fps if fps > 0 else 0
        if not cap.isOpened() or not math.isfinite(duration) or duration <= 0:
            raise ValueError("Downloaded video could not be decoded. Upload an H.264 MP4 instead.")
        if duration > MAX_DURATION_SECONDS or math.ceil(duration / item["interval"]) > MAX_FRAMES:
            raise ValueError("Video exceeds two hours or 2,000 frames. Use a wider frame interval.")
    finally:
        cap.release()
    if event.is_set():
        raise Interrupted
    update(item["id"], status="converting", title=result["title"])
    target = folder / "converted.mp4"

    def limit():
        if target.exists() and target.stat().st_size > MAX_UPLOAD_BYTES:
            raise ValueError("Converted video exceeds the 512 MB limit.")

    code = run_process(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-y",
            "-xerror",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-vf",
            "scale=w='trunc(min(1280,iw)/2)*2':h=-2",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(target),
        ],
        folder,
        event,
        900,
        limit,
    )
    limit()
    if code or not target.exists() or not target.stat().st_size:
        raise ValueError("Video conversion failed. Upload an H.264 MP4 instead.")
    return target, result["title"]


class Importer:
    def __init__(self):
        self.lock = threading.Lock()
        self.events = {}
        self.pool = None

    def create(self, url, interval):
        url = canonical_url(url)
        with self.lock:
            with store.connection() as db:
                existing = db.execute(
                    "SELECT id FROM videos WHERE source_url=? AND status!='removing'", (url,)
                ).fetchone()
                if existing:
                    return {"video_id": existing["id"], "duplicate": True}
                pending = db.execute(
                    "SELECT id FROM imports WHERE url=? AND status IN ('queued','downloading','converting')",
                    (url,),
                ).fetchone()
                if pending:
                    return {"id": pending["id"], "duplicate": True}
                if (
                    db.execute(
                        "SELECT COUNT(*) FROM imports WHERE status IN ('queued','downloading','converting')"
                    ).fetchone()[0]
                    >= 5
                ):
                    raise ValueError("Five links are already queued. Wait for one to finish.")
                job_id = uuid.uuid4().hex
                db.execute(
                    "INSERT INTO imports(id,url,interval) VALUES(?,?,?)", (job_id, url, interval)
                )
        self.submit(job_id)
        return {"id": job_id, "duplicate": False}

    def submit(self, job_id):
        with self.lock:
            if job_id in self.events:
                return False
            if self.pool is None:
                self.pool = ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="scenescout-import"
                )
            event = threading.Event()
            self.events[job_id] = event
            update(job_id, status="queued", error=None, downloaded=0)
            self.pool.submit(self._import, job_id, event)
        return True

    def _import(self, job_id, event):
        folder = DATA_DIR / "imports" / job_id
        try:
            item = job(job_id)
            if not item or event.is_set():
                raise Interrupted
            cleanup(job_id)
            folder.mkdir(parents=True)
            update(job_id, status="downloading")
            path, title = fetch_video(item, folder, event)
            # Hold the lock during publication so cancel cannot orphan an unexpected video.
            with self.lock:
                if event.is_set():
                    raise Interrupted
                video_id = publish(path, title, item["url"], item["interval"])
                update(job_id, status="completed", title=title, video_id=video_id)
        except Interrupted:
            item = job(job_id)
            if item and item["status"] != "removing":
                update(job_id, status="paused", error="Interrupted. Retry the link import.")
        except Exception as exc:
            logger.exception("Link import failed for %s", job_id)
            update(
                job_id,
                status="error",
                error=str(exc)[:500]
                if isinstance(exc, ValueError)
                else "Import failed. Retry or upload the video file.",
            )
        finally:
            try:
                item = job(job_id)
                cleanup(job_id, delete=bool(item and item["status"] == "removing"))
            except OSError:
                logger.exception("Temporary import cleanup failed")
            with self.lock:
                self.events.pop(job_id, None)

    def remove(self, job_id):
        with self.lock:
            update(job_id, status="removing")
            event = self.events.get(job_id)
            if event:
                event.set()
            else:
                cleanup(job_id, delete=True)

    def shutdown(self):
        with self.lock:
            for event in self.events.values():
                event.set()
            pool = self.pool
        if pool:
            pool.shutdown(wait=True, cancel_futures=True)
        with self.lock:
            for job_id in list(self.events):
                item = job(job_id)
                if item and item["status"] == "removing":
                    cleanup(job_id, delete=True)
                else:
                    update(job_id, status="paused", error="Interrupted. Retry the link import.")
            self.events.clear()
            self.pool = None


importer = Importer()
