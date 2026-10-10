"""Isolated yt-dlp worker. Only public YouTube/X extractors, no user config or cookies."""

import json
import os
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import imageio_ffmpeg
import yt_dlp

from .config import MAX_DURATION_SECONDS, MAX_FRAMES, MAX_UPLOAD_BYTES


def write_json(path, value):
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    # A Windows progress reader can briefly hold the destination without delete sharing.
    for delay in (0.02, 0.05, 0.1, 0.2):
        try:
            pending.replace(path)
            return
        except PermissionError:
            time.sleep(delay)
    pending.replace(path)


def runtime():
    custom = os.getenv("SCENESCOUT_DENO_PATH")
    bundled = Path.cwd() / ".bootstrap" / "deno.exe"
    deno = custom or (str(bundled) if bundled.is_file() else shutil.which("deno"))
    if deno:
        return {"deno": {"path": deno}}
    node = shutil.which("node")
    return {"node": {"path": node}} if node else {}


def download(url, folder, interval):
    def progress(data):
        # Separate video/audio streams must share the same budget and progress counter.
        size = max(
            data.get("downloaded_bytes", 0),
            sum(p.stat().st_size for p in folder.glob("source.*") if p.is_file()),
        )
        if size > MAX_UPLOAD_BYTES:
            raise ValueError("Video exceeds the 512 MB download limit.")
        write_json(folder / "progress.json", {"downloaded": size})

    def check(info, *, incomplete):
        duration = info.get("duration")
        if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
            raise ValueError("Live streams are not supported. Use a finished video.")
        if duration and (duration > MAX_DURATION_SECONDS or duration / interval > MAX_FRAMES):
            raise ValueError("Video exceeds two hours or 2,000 frames. Use a wider frame interval.")
        return None

    options = {
        "outtmpl": str(folder / "source.%(ext)s"),
        "format": "bv*[height<=720][vcodec^=avc1]+ba[ext=m4a]/b[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]",
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "playlist_items": "1",
        "max_filesize": MAX_UPLOAD_BYTES,
        "socket_timeout": 15,
        "retries": 2,
        "fragment_retries": 2,
        "concurrent_fragment_downloads": 1,
        "cachedir": False,
        "quiet": True,
        "noprogress": True,
        "progress_hooks": [progress],
        "match_filter": check,
        "js_runtimes": runtime(),
        "remote_components": set(),
        "allowed_extractors": ["youtube", "twitter", "twitter:amplify", "twitter:card"],
    }
    # Prevent installed yt-dlp plugins from adding executable code to this fixed import path.
    yt_dlp.globals.plugin_dirs.value = []
    fallback_used = False
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as exc:
        if urlsplit(url).hostname != "www.youtube.com" or "HTTP Error 403" not in str(exc):
            raise
        # One fresh attempt using the public HLS formats. Never use cookies or private clients.
        for path in folder.glob("source.*"):
            if path.is_file():
                path.unlink()
        write_json(folder / "progress.json", {"downloaded": 0})
        options["format"] = (
            "bv[height<=720][protocol^=m3u8]+ba[protocol^=m3u8]/b[height<=720][protocol^=m3u8]"
        )
        fallback_used = True
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
    if not info:
        raise ValueError("No downloadable public video was found.")
    if info.get("entries"):
        info = next((entry for entry in info["entries"] if entry), None)
    if not info:
        raise ValueError("This post has no video.")
    sources = [p for p in folder.glob("source.*") if p.suffix in {".mp4", ".webm", ".mkv"}]
    if len(sources) != 1:
        raise ValueError("Download incomplete or too large. Try a shorter public video.")
    if sources[0].stat().st_size > MAX_UPLOAD_BYTES:
        raise ValueError("Video exceeds the 512 MB download limit.")
    write_json(
        folder / "result.json",
        {
            "file": sources[0].name,
            "title": info.get("title", "Linked video")[:180],
            "hls_fallback": fallback_used,
        },
    )


if __name__ == "__main__":
    destination = Path(sys.argv[2])
    try:
        download(sys.argv[1], destination, float(sys.argv[3]))
    except Exception as exc:
        # Keep platform/CDN URLs and remote messages out of the API/UI.
        if isinstance(exc, ValueError):
            message = str(exc)
        elif isinstance(exc, OSError):
            message = "Temporary files could not be written. Check free disk space and folder permissions."
        else:
            message = (
                "Platform refused the download. The video may require sign-in, be unavailable, "
                "or the platform may have changed. Try a public video or upload its file."
            )
        write_json(destination / "error.json", {"error": message, "error_type": type(exc).__name__})
        raise SystemExit(1)
