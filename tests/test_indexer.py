import threading
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import pytest

from scenescout import indexer, store


@pytest.fixture
def media(add_video, library):
    def create(video_id="a"):
        add_video(video_id, "queued", interval=1)
        writer = cv2.VideoWriter(
            str(library / "videos" / f"{video_id}.mp4"),
            cv2.VideoWriter_fourcc(*"mp4v"),
            2,
            (32, 32),
        )
        assert writer.isOpened()
        for i in range(6):
            writer.write(np.full((32, 32, 3), i * 30, dtype=np.uint8))
        writer.release()

    return create


class FakeEncoder:
    def __init__(self, vector):
        self.vector = vector
        self.calls = 0
        self.fail_on = None

    def batch_size(self):
        return 1

    def encode_many(self, items):
        self.calls += len(items)
        if self.calls == self.fail_on:
            raise RuntimeError("temporary model failure")
        return np.stack([self.vector for _ in items])


def test_failed_index_resumes_without_reencoding_saved_frames(media, vector, monkeypatch):
    media()
    model = FakeEncoder(vector)
    model.fail_on = 2
    monkeypatch.setattr(indexer, "encoder", model)
    worker = indexer.Indexer()
    worker._index("a", threading.Event())
    assert store.video("a")["status"] == "error"
    assert store.video("a")["progress"] == 1
    model.fail_on = None
    worker._index("a", threading.Event())
    assert store.video("a")["status"] == "ready"
    assert store.video("a")["progress"] == 3
    assert model.calls == 4  # one saved frame, one failed attempt, two remaining frames


def test_missing_thumbnail_is_repaired_on_resume(media, library, vector, monkeypatch):
    media()
    store.checkpoint("a", [("a-00000", "a", 0, vector.tobytes())])
    model = FakeEncoder(vector)
    monkeypatch.setattr(indexer, "encoder", model)
    indexer.Indexer()._index("a", threading.Event())
    assert model.calls == 3
    assert (library / "thumbnails/a/a-00000.jpg").exists()
    assert store.video("a")["progress"] == 3


def test_shutdown_handles_cancelled_queued_removal_and_preserves_other_jobs(
    media, vector, monkeypatch
):
    for video_id in ["a", "b", "c"]:
        media(video_id)
    entered, release, closing = threading.Event(), threading.Event(), threading.Event()
    model = FakeEncoder(vector)

    def blocked(items):
        entered.set()
        assert release.wait(10)
        return np.stack([vector for _ in items])

    monkeypatch.setattr(model, "encode_many", blocked)
    monkeypatch.setattr(indexer, "encoder", model)
    worker = indexer.Indexer()
    try:
        assert worker.submit("a")
        assert entered.wait(10)
        assert not worker.submit("a")
        worker.submit("b")
        worker.submit("c")
        worker.remove("b")
        real_shutdown = worker.pool.shutdown

        def shutdown_pool(**kwargs):
            closing.set()
            real_shutdown(**kwargs)

        monkeypatch.setattr(worker.pool, "shutdown", shutdown_pool)
        with ThreadPoolExecutor(max_workers=1) as closer:
            future = closer.submit(worker.shutdown)
            assert closing.wait(10)
            release.set()
            future.result(timeout=10)
        assert store.video("a")["status"] == "paused"
        assert store.video("b") is None
        assert store.video("c")["status"] == "paused"
    finally:
        release.set()
        worker.shutdown()


def test_corrupt_video_does_not_publish_index(add_video, library, monkeypatch, vector):
    add_video("a", "queued")
    (library / "videos/a.mp4").write_bytes(b"not a video")
    monkeypatch.setattr(indexer, "encoder", FakeEncoder(vector))
    indexer.Indexer()._index("a", threading.Event())
    assert store.video("a")["status"] == "error"
    assert store.video("a")["progress"] == 0
