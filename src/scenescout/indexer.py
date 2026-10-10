"""Sample video frames, preserve timecodes, and publish searchable indexes atomically."""

import logging
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
from PIL import Image

from . import store
from .config import DATA_DIR, MAX_DURATION_SECONDS, MAX_FRAMES
from .encoder import encoder

logger = logging.getLogger(__name__)


class Indexer:
    def __init__(self):
        self.pool = None
        self.events = {}
        self.deletions = set()
        self.lock = threading.Lock()

    def submit(self, video_id):
        event = threading.Event()
        with self.lock:
            if video_id in self.events:
                return False
            if self.pool is None:
                self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scenescout-index")
            store.update(video_id, status="queued", error=None)
            self.events[video_id] = event
            self.pool.submit(self._index, video_id, event)
        return True

    def cancel(self, video_id):
        with self.lock:
            event = self.events.get(video_id)
        if event:
            event.set()

    def shutdown(self):
        with self.lock:
            for event in self.events.values():
                event.set()
            pool = self.pool
        if pool:
            pool.shutdown(wait=True, cancel_futures=True)
        # Cancelled queued futures never enter the worker's finally block.
        with self.lock:
            pending = list(self.events)
            deletions = self.deletions.copy()
            self.events.clear()
            self.deletions.clear()
            self.pool = None
        for video_id in pending:
            if video_id in deletions:
                store.remove(video_id)
            else:
                store.update(video_id, status="paused", error="Interrupted. Resume saved frames.")

    def _index(self, video_id, event):
        started = time.perf_counter()
        cap = None
        item = None
        thumb_dir = DATA_DIR / "thumbnails" / video_id
        try:
            item = store.video(video_id)
            if not item or event.is_set():
                return
            store.update(video_id, status="indexing")
            cap = cv2.VideoCapture(str(DATA_DIR / "videos" / f"{video_id}{item['extension']}"))
            fps = cap.get(cv2.CAP_PROP_FPS)
            count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if (
                not cap.isOpened()
                or not math.isfinite(fps)
                or fps <= 0
                or not math.isfinite(count)
                or count <= 0
            ):
                raise ValueError(
                    "Cannot decode this video. Export it as an H.264 MP4 and import it again."
                )
            duration = count / fps
            if duration > MAX_DURATION_SECONDS:
                raise ValueError(
                    "Videos must be shorter than two hours. Split this video before importing."
                )
            total = math.ceil(duration / item["interval"])
            if total > MAX_FRAMES:
                raise ValueError("Too many frames. Import again using a wider sampling interval.")
            store.update(video_id, duration=duration, total=total)
            thumb_dir.mkdir(parents=True, exist_ok=True)
            with store.connection() as db:
                completed = {
                    row["id"]
                    for row in db.execute("SELECT id FROM scenes WHERE video_id=?", (video_id,))
                }
            batch = []

            def commit_batch():
                vectors = encoder.encode_many([{"image": image} for _, _, image in batch])
                if event.is_set():
                    return
                scenes = []
                for (scene_id, timestamp, image), vector in zip(batch, vectors, strict=True):
                    thumb = image.copy()
                    thumb.thumbnail((480, 300))
                    thumb.save(thumb_dir / f"{scene_id}.jpg", quality=85)
                    scenes.append((scene_id, video_id, timestamp, vector.astype("<f4").tobytes()))
                store.checkpoint(video_id, scenes)
                batch.clear()

            for index in range(total):
                if event.is_set():
                    return
                scene_id = f"{video_id}-{index:05d}"
                if scene_id in completed and (thumb_dir / f"{scene_id}.jpg").exists():
                    continue
                timestamp = index * item["interval"]
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                ok, frame = cap.read()
                if not ok:
                    raise ValueError(
                        f"Video decoding stopped at {timestamp:.1f}s. Try an H.264 MP4 export."
                    )
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image.thumbnail((768, 768))
                batch.append((scene_id, timestamp, image))
                if len(batch) >= encoder.batch_size():
                    commit_batch()
            if batch and not event.is_set():
                commit_batch()
            if not event.is_set():
                store.update(
                    video_id,
                    status="ready",
                    error=None,
                    elapsed=round(item["elapsed"] + time.perf_counter() - started, 2),
                )
        except Exception as exc:
            logger.exception("Indexing failed for %s", video_id)
            if not event.is_set():
                message = (
                    str(exc)
                    if isinstance(exc, ValueError)
                    else "Indexing failed. Check the server log, RAM and model download, then resume."
                )
                store.update(video_id, status="error", error=message[:500])
        finally:
            if cap:
                cap.release()
            with self.lock:
                self.events.pop(video_id, None)
                deleting = video_id in self.deletions
                self.deletions.discard(video_id)
            if event.is_set():
                if deleting:
                    # The worker owns cleanup so deletion cannot race in-flight inference.
                    store.remove(video_id)
                else:
                    store.update(
                        video_id,
                        status="paused",
                        elapsed=round(item["elapsed"] + time.perf_counter() - started, 2)
                        if item
                        else 0,
                        error="Indexing interrupted. Resume to continue from saved frames.",
                    )

    def remove(self, video_id):
        with self.lock:
            active = video_id in self.events
            store.update(video_id, status="removing")
            if active:
                self.deletions.add(video_id)
                self.events[video_id].set()
        if not active:
            store.remove(video_id)


indexer = Indexer()
