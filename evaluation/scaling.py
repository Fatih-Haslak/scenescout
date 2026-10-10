"""Measure a full real video and synthetic exact-vector scan scaling separately."""

import hashlib
import json
import os
import shutil
import threading
import time
from pathlib import Path

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parent.parent


def stats(values):
    return {
        "p50_ms": float(np.median(values)),
        "p95_ms": float(np.percentile(values, 95)),
        "samples": len(values),
    }


def main():
    data = ROOT / "work" / "scaling-run" / str(time.time_ns())
    os.environ["SCENESCOUT_DATA_DIR"] = str(data)
    os.environ["SCENESCOUT_DEVICE"] = "cuda"
    os.environ["SCENESCOUT_BATCH_SIZE"] = "2"
    import torch
    from scenescout import store
    from scenescout.encoder import encoder
    from scenescout.indexer import Indexer
    from scenescout.retrieval import Retrieval, rank

    store.initialize()
    source = ROOT / "examples/.cache/big-buck-bunny.mp4"
    shutil.copyfile(source, data / "videos/full.mp4")
    with store.connection() as db:
        db.execute(
            "INSERT INTO videos(id,name,extension,digest,size,interval) VALUES(?,?,?,?,?,?)",
            (
                "full",
                "Big Buck Bunny full",
                ".mp4",
                hashlib.sha256(source.read_bytes()).hexdigest(),
                source.stat().st_size,
                3,
            ),
        )
    encoder.encode("a rabbit", "SearchQuery")
    started = time.perf_counter()
    Indexer()._index("full", threading.Event())
    full = store.video("full")
    if full["status"] != "ready":
        raise RuntimeError(full["error"])
    full_result = {
        "duration_seconds": full["duration"],
        "frames": full["progress"],
        "index_seconds_model_already_loaded": time.perf_counter() - started,
        "device": encoder.device,
        "cuda_peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
    }
    store.remove("full")
    rng = np.random.default_rng(20261010)
    query = rng.normal(size=768).astype(np.float32)
    query /= np.linalg.norm(query)
    scaling = []
    for size in [1000, 10000, 50000]:
        for item in store.videos():
            store.remove(item["id"])
        for offset in range(0, size, 2000):
            video_id = f"synthetic-{offset}"
            count = min(2000, size - offset)
            with store.connection() as db:
                db.execute(
                    "INSERT INTO videos(id,name,extension,digest,size,interval,status,duration) VALUES(?,?,?,?,?,?,?,?)",
                    (video_id, video_id, ".mp4", video_id, 1, 3, "ready", count * 3),
                )
            vectors = rng.normal(size=(count, 768)).astype(np.float32)
            vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
            store.checkpoint(
                video_id,
                [
                    (f"{video_id}-{i:05d}", video_id, i * 3, vectors[i].astype("<f4").tobytes())
                    for i in range(count)
                ],
            )
        store.invalidate()
        cache = Retrieval()
        started = time.perf_counter()
        rows, matrix = cache.snapshot()
        cold_ms = (time.perf_counter() - started) * 1000
        warm, uncached = [], []
        for _ in range(20):
            started = time.perf_counter()
            rows, matrix = cache.snapshot()
            rank(rows, matrix, query)
            warm.append((time.perf_counter() - started) * 1000)
        for _ in range(5):
            fresh = Retrieval()
            started = time.perf_counter()
            rows, matrix = fresh.snapshot()
            rank(rows, matrix, query)
            uncached.append((time.perf_counter() - started) * 1000)
        scaling.append(
            {
                "vectors": size,
                "raw_matrix_mib": matrix.nbytes / 1024**2,
                "first_snapshot_ms": cold_ms,
                "warm_cached_exact_rank": stats(warm),
                "uncached_snapshot_plus_rank": stats(uncached),
                "process_rss_mib_after_size": psutil.Process().memory_info().rss / 1024**2,
            }
        )
        print(
            f"Synthetic {size}: cached {np.median(warm):.2f}ms; uncached {np.median(uncached):.2f}ms",
            flush=True,
        )
    report = {
        "full_video": full_result,
        "synthetic_retrieval": scaling,
        "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "limitations": [
            "Full-video throughput is one run of one animated film, no quality labels.",
            "Synthetic vectors measure CPU exact scan/cache costs, not retrieval quality or media indexing.",
            "RSS includes the loaded model and allocator retention; it is not per-query memory.",
            "Timing excludes model load, installation, download, HTTP and UI.",
        ],
    }
    (ROOT / "evaluation/scaling-results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
