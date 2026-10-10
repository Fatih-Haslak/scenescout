"""Loopback-only web application, streamed uploads, and documented search endpoints."""

import hashlib
import io
import logging
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from . import store
from .config import DATA_DIR, MAX_UPLOAD_BYTES, STATIC_DIR
from .encoder import encoder
from .indexer import indexer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    store.initialize()
    yield
    indexer.shutdown()


app = FastAPI(
    title="SceneScout",
    version="0.1.0",
    lifespan=lifespan,
    description="Local visual video search using Google EmbeddingGemma 2.",
    docs_url=None,
    redoc_url=None,
)


@app.middleware("http")
async def local_only(request: Request, call_next):
    host = request.url.hostname
    if host not in {"127.0.0.1", "localhost", "::1"}:
        return JSONResponse(
            {"detail": "SceneScout accepts loopback requests only."}, status_code=403
        )
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        return JSONResponse({"detail": "Cross-origin requests are disabled."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' blob:; media-src 'self' blob:; "
        "style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
    )
    return response


def require_video(video_id):
    item = store.video(video_id)
    if not item:
        raise HTTPException(404, "Video not found")
    return item


@app.get("/api/status")
def status():
    return {
        "model": encoder.status(),
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
        "version": "0.1.0",
        "mode": "visual_frames",
    }


@app.get("/api/videos")
def list_videos():
    return store.videos()


@app.post("/api/videos", status_code=202)
async def upload_video(file: UploadFile = File(...), interval: float = Form(3.0)):
    extension = Path(file.filename or "video.mp4").suffix.lower()
    if extension not in {".mp4", ".webm"}:
        raise HTTPException(400, "Use an MP4 or WebM video. H.264 MP4 is recommended.")
    if not np.isfinite(interval) or not 1 <= interval <= 30:
        raise HTTPException(400, "Sampling interval must be between 1 and 30 seconds.")
    video_id = uuid.uuid4().hex
    path = DATA_DIR / "videos" / f"{video_id}{extension}"
    size = 0
    digest = hashlib.sha256()
    try:
        with path.open("xb") as target:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        413, "Video is larger than 512 MB. Split or compress it first."
                    )
                digest.update(chunk)
                target.write(chunk)
        if not size:
            raise HTTPException(400, "The file is empty.")
        with store.connection() as db:
            existing = db.execute(
                "SELECT id FROM videos WHERE digest=?", (digest.hexdigest(),)
            ).fetchone()
            if existing:
                path.unlink()
                return {"id": existing["id"], "duplicate": True}
            name = (file.filename or "video.mp4").replace("\\", "/").split("/")[-1][:180]
            db.execute(
                "INSERT INTO videos(id,name,extension,digest,size,interval) VALUES(?,?,?,?,?,?)",
                (video_id, name, extension, digest.hexdigest(), size, interval),
            )
        indexer.submit(video_id)
        return {"id": video_id, "duplicate": False}
    except sqlite3.IntegrityError:
        path.unlink(missing_ok=True)
        with store.connection() as db:
            existing = db.execute(
                "SELECT id FROM videos WHERE digest=?", (digest.hexdigest(),)
            ).fetchone()
        if existing:
            return {"id": existing["id"], "duplicate": True}
        raise
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


@app.delete("/api/videos/{video_id}", status_code=202)
def delete_video(video_id: str):
    require_video(video_id)
    indexer.remove(video_id)
    return {"status": "removing"}


@app.get("/api/videos/{video_id}/media")
def video_media(video_id: str):
    item = require_video(video_id)
    mime = "video/mp4" if item["extension"] == ".mp4" else "video/webm"
    return FileResponse(DATA_DIR / "videos" / f"{video_id}{item['extension']}", media_type=mime)


@app.get("/api/videos/{video_id}/scenes")
def video_scenes(video_id: str):
    require_video(video_id)
    with store.connection() as db:
        rows = list(
            db.execute(
                "SELECT id,timestamp FROM scenes WHERE video_id=? ORDER BY timestamp", (video_id,)
            )
        )
    # Cap the filmstrip, sampling evenly across the whole recording.
    indices = np.linspace(0, len(rows) - 1, min(80, len(rows)), dtype=int) if rows else []
    return [
        {
            "id": rows[i]["id"],
            "timestamp": rows[i]["timestamp"],
            "thumbnail": f"/api/thumbnails/{rows[i]['id']}",
        }
        for i in indices
    ]


@app.get("/api/thumbnails/{scene_id}")
def thumbnail(scene_id: str):
    with store.connection() as db:
        row = db.execute("SELECT video_id FROM scenes WHERE id=?", (scene_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Scene not found")
    return FileResponse(
        DATA_DIR / "thumbnails" / row["video_id"] / f"{scene_id}.jpg", media_type="image/jpeg"
    )


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    video_id: str | None = None
    limit: int = Field(default=12, ge=1, le=30)


def search(vector_content, video_id, limit, prompt_name=None):
    started = time.perf_counter()
    with store.connection() as db:
        sql = """SELECT s.id,s.video_id,s.timestamp,s.vector,v.name,v.duration,v.interval
                 FROM scenes s JOIN videos v ON v.id=s.video_id WHERE v.status='ready'"""
        params = ()
        if video_id:
            require_video(video_id)
            sql += " AND v.id=?"
            params = (video_id,)
        rows = list(db.execute(sql, params))
    if not rows:
        return {"results": [], "elapsed_ms": 0, "searched_frames": 0}
    try:
        vector = encoder.encode(vector_content, prompt_name)
    except Exception as exc:
        logger.exception("Search inference failed")
        raise HTTPException(
            503, "Model inference failed. Check the server log and available RAM."
        ) from exc
    matrix = np.stack([np.frombuffer(row["vector"], dtype="<f4") for row in rows])
    scores = matrix @ vector
    picked = []
    for index in np.argsort(-scores):
        row = rows[index]
        # Adjacent sampled frames often repeat the same moment. Keep a diverse shortlist.
        if any(
            item["video_id"] == row["video_id"]
            and abs(item["timestamp"] - row["timestamp"]) < row["interval"] * 2
            for item in picked
        ):
            continue
        picked.append(
            {
                "id": row["id"],
                "video_id": row["video_id"],
                "name": row["name"],
                "timestamp": row["timestamp"],
                "duration": row["duration"],
                "score": round(float(scores[index]), 4),
                "thumbnail": f"/api/thumbnails/{row['id']}",
            }
        )
        if len(picked) == limit:
            break
    return {
        "results": picked,
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "searched_frames": len(rows),
    }


@app.post("/api/search")
def text_search(body: SearchRequest):
    query = body.query.strip()
    if not query:
        raise HTTPException(400, "Describe the scene you are looking for.")
    return search(query, body.video_id, body.limit, "SearchQuery")


@app.post("/api/search/image")
def image_search(file: UploadFile = File(...), video_id: str | None = Form(None)):
    raw = file.file.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(413, "Reference image must be smaller than 8 MB.")
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.width * source.height > 20_000_000:
                raise HTTPException(400, "Reference image is too large. Resize it first.")
            source.thumbnail((768, 768))
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(400, "Use a valid JPEG, PNG or WebP image.") from exc
    finally:
        file.file.close()
    return search({"image": image}, video_id, 12)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/docs", include_in_schema=False)
def api_docs():
    return FileResponse(STATIC_DIR / "api.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
