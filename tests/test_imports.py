import json
import sys
import threading
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from scenescout import api, imports, link_download, store


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://youtu.be/YE7VzlLtp-4?si=tracking", "https://www.youtube.com/watch?v=YE7VzlLtp-4"),
        (
            "https://m.youtube.com/watch?v=YE7VzlLtp-4&list=ignored",
            "https://www.youtube.com/watch?v=YE7VzlLtp-4",
        ),
        (
            "https://www.youtube.com/shorts/YE7VzlLtp-4",
            "https://www.youtube.com/watch?v=YE7VzlLtp-4",
        ),
        ("https://youtube.com/live/YE7VzlLtp-4", "https://www.youtube.com/watch?v=YE7VzlLtp-4"),
        (
            "https://twitter.com/NASA/status/123/video/2?s=20",
            "https://x.com/NASA/status/123/video/2",
        ),
        ("https://x.com/i/web/status/123", "https://x.com/i/web/status/123"),
    ],
)
def test_canonical_single_video_links(url, expected):
    assert imports.canonical_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://www.youtube.com/watch?v=YE7VzlLtp-4",
        "https://127.0.0.1/private",
        "https://youtube.com.evil.example/watch?v=YE7VzlLtp-4",
        "https://user:password@youtube.com/watch?v=YE7VzlLtp-4",
        "https://youtube.com:444/watch?v=YE7VzlLtp-4",
        "https://youtube.com:bad/watch?v=YE7VzlLtp-4",
        "https://youtube.com/playlist?list=PLsomething",
        "https://youtube.com/watch?v=short",
        "file:///C:/private.mp4",
        "https://x.com/NASA",
        "https://x.com/NASA/status/abc",
    ],
)
def test_invalid_or_private_network_links_are_rejected(url):
    with pytest.raises(ValueError, match="YouTube"):
        imports.canonical_url(url)


@pytest.fixture
def worker(library):
    imports.initialize()
    result = imports.Importer()
    yield result
    result.shutdown()


@pytest.fixture
def client(library, worker, monkeypatch):
    monkeypatch.setattr(api, "importer", worker)
    monkeypatch.setattr(worker, "submit", lambda job_id: True)
    with TestClient(api.app, base_url="http://127.0.0.1:8765") as client:
        yield client


def test_link_api_validation_dedup_retry_and_removal(client, worker):
    assert client.post("/api/imports", json={"url": "https://127.0.0.1/video"}).status_code == 400
    assert (
        client.post(
            "/api/imports", json={"url": "https://youtu.be/YE7VzlLtp-4", "interval": 31}
        ).status_code
        == 422
    )
    first = client.post("/api/imports", json={"url": "https://youtu.be/YE7VzlLtp-4"}).json()
    second = client.post(
        "/api/imports", json={"url": "https://youtube.com/watch?v=YE7VzlLtp-4"}
    ).json()
    assert second == {"id": first["id"], "duplicate": True}
    assert len(client.get("/api/imports").json()) == 1
    assert client.post(f"/api/imports/{first['id']}/retry").status_code == 409
    imports.update(first["id"], status="error")
    assert client.post(f"/api/imports/{first['id']}/retry").status_code == 202
    assert client.delete(f"/api/imports/{first['id']}").status_code == 202
    assert client.get("/api/imports").json() == []
    assert client.post("/api/imports/missing/retry").status_code == 404
    assert client.delete("/api/imports/missing").status_code == 404
    with pytest.raises(ValueError):
        imports.update("missing", invalid="value")


def test_import_queue_limit_and_existing_source(client, add_video):
    for number in range(5):
        assert (
            client.post(
                "/api/imports", json={"url": f"https://x.com/NASA/status/{number}"}
            ).status_code
            == 202
        )
    assert (
        client.post("/api/imports", json={"url": "https://x.com/NASA/status/6"}).status_code == 400
    )
    add_video()
    with store.connection() as db:
        db.execute("UPDATE videos SET source_url=? WHERE id='a'", ("https://x.com/NASA/status/7",))
    assert client.post("/api/imports", json={"url": "https://x.com/NASA/status/7"}).json() == {
        "video_id": "a",
        "duplicate": True,
    }


def test_completed_link_publish_is_atomic_and_deduplicates(library, monkeypatch):
    calls = []
    monkeypatch.setattr(imports.indexer, "submit", lambda video_id: calls.append(video_id))
    path = library / "input.mp4"
    path.write_bytes(b"video bytes")
    video_id = imports.publish(path, "Title", "https://x.com/NASA/status/1", 3)
    item = store.video(video_id)
    assert item["source_url"] == "https://x.com/NASA/status/1"
    assert item["name"] == "Title"
    assert not path.exists()
    duplicate = library / "duplicate.mp4"
    duplicate.write_bytes(b"video bytes")
    assert imports.publish(duplicate, "Duplicate", "https://x.com/NASA/status/2", 3) == video_id
    assert len(store.videos()) == 1
    assert calls == [video_id]


def test_actual_conversion_and_publication(library, worker, monkeypatch):
    monkeypatch.setattr(worker, "submit", lambda job_id: True)
    item = worker.create("https://youtu.be/YE7VzlLtp-4", 3)
    original = imports.run_process

    def command_runner(command, folder, event, timeout, progress=None):
        if "scenescout.link_download" not in command:
            return original(command, folder, event, timeout, progress)
        writer = cv2.VideoWriter(
            str(folder / "source.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 2, (32, 32)
        )
        assert writer.isOpened()
        for _ in range(4):
            writer.write(np.full((32, 32, 3), 150, dtype=np.uint8))
        writer.release()
        (folder / "result.json").write_text(
            json.dumps({"file": "source.mp4", "title": "Converted clip"}), encoding="utf-8"
        )
        return 0

    monkeypatch.setattr(imports, "run_process", command_runner)
    monkeypatch.setattr(imports.indexer, "submit", lambda video_id: True)
    worker._import(item["id"], threading.Event())
    saved = imports.job(item["id"])
    assert saved["status"] == "completed"
    video = store.video(saved["video_id"])
    assert video["source_url"] == "https://www.youtube.com/watch?v=YE7VzlLtp-4"
    assert (library / "videos" / f"{video['id']}.mp4").exists()
    assert not (library / "imports" / item["id"]).exists()


def test_download_error_preserves_retry_and_cleans_temporary_files(library, worker, monkeypatch):
    monkeypatch.setattr(worker, "submit", lambda job_id: True)
    item = worker.create("https://x.com/NASA/status/1", 3)

    def failure(command, folder, event, timeout, progress=None):
        (folder / "error.json").write_text(
            '{"error":"Platform refused the download."}', encoding="utf-8"
        )
        return 1

    monkeypatch.setattr(imports, "run_process", failure)
    worker._import(item["id"], threading.Event())
    assert imports.job(item["id"])["status"] == "error"
    assert "Platform refused" in imports.job(item["id"])["error"]
    assert store.videos() == []
    assert not (library / "imports" / item["id"]).exists()


def test_cancel_and_shutdown_stop_active_and_queued_jobs(worker, monkeypatch):
    entered = threading.Event()
    stopped = threading.Event()

    def blocked(item, folder, event):
        entered.set()
        assert event.wait(5)
        stopped.set()
        raise imports.Interrupted

    monkeypatch.setattr(imports, "fetch_video", blocked)
    first = worker.create("https://x.com/NASA/status/1", 3)
    assert entered.wait(5)
    assert not worker.submit(first["id"])
    second = worker.create("https://x.com/NASA/status/2", 3)
    third = worker.create("https://x.com/NASA/status/3", 3)
    worker.remove(first["id"])
    worker.remove(second["id"])
    worker.shutdown()
    assert stopped.is_set()
    assert imports.job(first["id"]) is None
    assert imports.job(second["id"]) is None
    assert imports.job(third["id"])["status"] == "paused"
    assert worker.pool is None
    assert not worker.events


def test_restart_preserves_interrupted_import_and_removal(library, worker, monkeypatch):
    monkeypatch.setattr(worker, "submit", lambda job_id: True)
    first = worker.create("https://x.com/NASA/status/1", 3)
    second = worker.create("https://x.com/NASA/status/2", 3)
    imports.update(first["id"], status="converting")
    imports.update(second["id"], status="removing")
    folder = library / "imports" / second["id"]
    folder.mkdir()
    (folder / "partial.mp4").write_bytes(b"partial")
    store.initialize()
    imports.initialize()
    assert imports.job(first["id"])["status"] == "paused"
    assert imports.job(second["id"]) is None
    assert not folder.exists()


def test_child_cancellation_and_timeout_reap_process(tmp_path):
    event = threading.Event()
    event.set()
    with pytest.raises(imports.Interrupted):
        imports.run_process(
            [sys.executable, "-c", "import time; time.sleep(10)"], tmp_path, event, 10
        )
    with pytest.raises(ValueError, match="timed out"):
        imports.run_process(
            [sys.executable, "-c", "import time; time.sleep(10)"], tmp_path, threading.Event(), 0
        )
    assert imports.run_process([sys.executable, "-c", "pass"], tmp_path, threading.Event(), 5) == 0


def test_link_runtime_and_downloader_limits(tmp_path, monkeypatch):
    monkeypatch.setenv("SCENESCOUT_DENO_PATH", "C:/runtime/deno.exe")
    assert link_download.runtime() == {"deno": {"path": "C:/runtime/deno.exe"}}
    monkeypatch.delenv("SCENESCOUT_DENO_PATH")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        link_download.shutil, "which", lambda name: "/usr/bin/node" if name == "node" else None
    )
    assert link_download.runtime() == {"node": {"path": "/usr/bin/node"}}
    options = []

    class Downloader:
        def __init__(self, config):
            options.append(config)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def extract_info(self, *_args, **_kwargs):
            config = options[-1]
            (tmp_path / "source.mp4").write_bytes(b"media")
            config["progress_hooks"][0]({"downloaded_bytes": 5})
            config["match_filter"]({"duration": 3}, incomplete=False)
            return {"title": "Real title"}

    monkeypatch.setattr(link_download.yt_dlp, "YoutubeDL", Downloader)
    link_download.download("https://x.com/NASA/status/1", tmp_path, 3)
    config = options[-1]
    assert "cookiefile" not in config and "cookiesfrombrowser" not in config
    assert config["noplaylist"] and config["remote_components"] == set()
    assert "generic" not in config["allowed_extractors"]
    assert json.loads((tmp_path / "result.json").read_text())["title"] == "Real title"
    with pytest.raises(ValueError, match="Live"):
        config["match_filter"]({"is_live": True}, incomplete=False)
    with pytest.raises(ValueError, match="two hours"):
        config["match_filter"]({"duration": 8000}, incomplete=False)
    with pytest.raises(ValueError, match="512 MB"):
        config["progress_hooks"][0]({"downloaded_bytes": link_download.MAX_UPLOAD_BYTES + 1})


@pytest.mark.parametrize("fail_again", [False, True])
def test_youtube_403_uses_one_fresh_hls_attempt(tmp_path, monkeypatch, fail_again):
    calls = []
    unrelated = tmp_path / "keep.txt"
    unrelated.write_text("keep")

    class Downloader:
        def __init__(self, config):
            calls.append(dict(config))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def extract_info(self, url, download):
            assert download
            if len(calls) == 1:
                (tmp_path / "source.f140.m4a.part").write_bytes(b"partial")
                raise link_download.yt_dlp.utils.DownloadError("HTTP Error 403: Forbidden")
            assert not list(tmp_path.glob("source.*"))
            assert json.loads((tmp_path / "progress.json").read_text())["downloaded"] == 0
            if fail_again:
                raise link_download.yt_dlp.utils.DownloadError("HTTP Error 403: Forbidden")
            (tmp_path / "source.mp4").write_bytes(b"complete")
            return {"title": "Public video"}

    monkeypatch.setattr(link_download.yt_dlp, "YoutubeDL", Downloader)
    if fail_again:
        with pytest.raises(link_download.yt_dlp.utils.DownloadError):
            link_download.download("https://www.youtube.com/watch?v=YE7VzlLtp-4", tmp_path, 3)
        assert not (tmp_path / "result.json").exists()
    else:
        link_download.download("https://www.youtube.com/watch?v=YE7VzlLtp-4", tmp_path, 3)
        assert json.loads((tmp_path / "result.json").read_text())["hls_fallback"]
    assert len(calls) == 2
    assert "protocol^=m3u8" not in calls[0]["format"]
    assert "protocol^=m3u8" in calls[1]["format"]
    for key in ["max_filesize", "allowed_extractors", "match_filter", "js_runtimes"]:
        assert calls[0][key] == calls[1][key]
    assert unrelated.read_text() == "keep"


@pytest.mark.parametrize(
    "url,error",
    [
        ("https://x.com/NASA/status/1", "HTTP Error 403: Forbidden"),
        ("https://www.youtube.com/watch?v=YE7VzlLtp-4", "Sign in to confirm your age"),
        ("https://www.youtube.com/watch?v=YE7VzlLtp-4", "HTTP Error 503"),
    ],
)
def test_unrelated_platform_errors_are_not_retried(tmp_path, monkeypatch, url, error):
    calls = []

    class Downloader:
        def __init__(self, config):
            calls.append(config)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def extract_info(self, *_args, **_kwargs):
            raise link_download.yt_dlp.utils.DownloadError(error)

    monkeypatch.setattr(link_download.yt_dlp, "YoutubeDL", Downloader)
    with pytest.raises(link_download.yt_dlp.utils.DownloadError):
        link_download.download(url, tmp_path, 3)
    assert len(calls) == 1


def test_download_streams_share_size_budget(tmp_path, monkeypatch):
    class Downloader:
        def __init__(self, config):
            self.progress = config["progress_hooks"][0]

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def extract_info(self, *_args, **_kwargs):
            (tmp_path / "source.f136.mp4").write_bytes(b"12345678")
            (tmp_path / "source.f140.m4a.part").write_bytes(b"1234")
            self.progress({"downloaded_bytes": 4})

    monkeypatch.setattr(link_download, "MAX_UPLOAD_BYTES", 10)
    monkeypatch.setattr(link_download.yt_dlp, "YoutubeDL", Downloader)
    with pytest.raises(ValueError, match="512 MB"):
        link_download.download("https://www.youtube.com/watch?v=YE7VzlLtp-4", tmp_path, 3)
    assert not (tmp_path / "result.json").exists()


def test_progress_write_recovers_from_transient_windows_reader_lock(tmp_path, monkeypatch):
    original = Path.replace
    calls = []

    def locked(path, destination):
        calls.append(path)
        if len(calls) < 3:
            raise PermissionError("reader is closing")
        return original(path, destination)

    monkeypatch.setattr(Path, "replace", locked)
    monkeypatch.setattr(link_download.time, "sleep", lambda delay: None)
    link_download.write_json(tmp_path / "progress.json", {"downloaded": 10})
    assert json.loads((tmp_path / "progress.json").read_text()) == {"downloaded": 10}
    assert not (tmp_path / "progress.tmp").exists()
