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
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scenescout-index")
        self.events = {}
        self.deletions = set()
        self.lock = threading.Lock()

    def submit(self, video_id):
        event = threading.Event()
        with self.lock:
            self.events[video_id] = event
        self.pool.submit(self._index, video_id, event)

    def cancel(self, video_id):
        with self.lock:
            event = self.events.get(video_id)
        if event:
            event.set()

    def shutdown(self):
        with self.lock:
            for event in self.events.values():
                event.set()
        self.pool.shutdown(wait=True, cancel_futures=True)

    def _index(self, video_id, event):
        started = time.perf_counter()
        cap = None
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
            progress = 0
            for index in range(total):
                if event.is_set():
                    return
                timestamp = index * item["interval"]
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                ok, frame = cap.read()
                if not ok:
                    raise ValueError(
                        f"Video decoding stopped at {timestamp:.1f}s. Try an H.264 MP4 export."
                    )
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image.thumbnail((768, 768))
                vector = encoder.encode({"image": image})
                if event.is_set():
                    return
                scene_id = f"{video_id}-{index:05d}"
                thumb = image.copy()
                thumb.thumbnail((480, 300))
                thumb.save(thumb_dir / f"{scene_id}.jpg", quality=85)
                with store.connection() as db:
                    db.execute(
                        "INSERT INTO scenes VALUES (?,?,?,?)",
                        (scene_id, video_id, timestamp, vector.astype("<f4").tobytes()),
                    )
                progress += 1
                store.update(video_id, progress=progress)
            if not event.is_set():
                store.update(
                    video_id, status="ready", elapsed=round(time.perf_counter() - started, 2)
                )
        except Exception as exc:
            logger.exception("Indexing failed for %s", video_id)
            if not event.is_set():
                message = (
                    str(exc)
                    if isinstance(exc, ValueError)
                    else "Indexing failed. Check the server log, RAM and model download. Remove and import again."
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
                    self._remove(video_id)
                else:
                    store.update(
                        video_id,
                        status="error",
                        error="Indexing interrupted. Remove and import again.",
                    )

    def remove(self, video_id):
        with self.lock:
            active = video_id in self.events
            if active:
                self.deletions.add(video_id)
                self.events[video_id].set()
        if active:
            store.update(video_id, status="removing")
        else:
            self._remove(video_id)

    @staticmethod
    def _remove(video_id):
        import shutil

        item = store.video(video_id)
        if not item:
            return
        with store.connection() as db:
            db.execute("DELETE FROM videos WHERE id=?", (video_id,))
        (DATA_DIR / "videos" / f"{video_id}{item['extension']}").unlink(missing_ok=True)
        shutil.rmtree(DATA_DIR / "thumbnails" / video_id, ignore_errors=True)


indexer = Indexer()
