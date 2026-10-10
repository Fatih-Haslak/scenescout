"""Reproducible real-model retrieval evaluation. Uses its own data directory."""

import argparse
import hashlib
import json
import os
import platform
import shutil
import threading
import time
from pathlib import Path

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=["cpu", "cuda"], required=True)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    data = (
        ROOT.parent / "work" / f"evaluation-{args.device}-b{args.batch_size}" / str(time.time_ns())
    )
    os.environ["SCENESCOUT_DATA_DIR"] = str(data)
    os.environ["SCENESCOUT_DEVICE"] = args.device
    os.environ["SCENESCOUT_BATCH_SIZE"] = str(args.batch_size)
    import torch
    from scenescout import api, store
    from scenescout.config import MODEL_REVISION
    from scenescout.encoder import encoder
    from scenescout.indexer import Indexer

    annotation_bytes = (ROOT / "queries.json").read_bytes()
    annotation = json.loads(annotation_bytes)
    media_manifest = json.loads((ROOT / "media-manifest.json").read_text(encoding="utf-8"))
    store.initialize()
    started = time.perf_counter()
    encoder.encode(annotation["cases"][0]["en"], "SearchQuery")
    cold_query_ms = (time.perf_counter() - started) * 1000
    indexes = []
    worker = Indexer()
    for media in media_manifest:
        video_id = media["id"]
        source = ROOT / "media" / f"{video_id}.mp4"
        assert hashlib.sha256(source.read_bytes()).hexdigest() == media["sha256"]
        shutil.copyfile(source, data / "videos" / f"{video_id}.mp4")
        with store.connection() as db:
            db.execute(
                """INSERT INTO videos(id,name,extension,digest,size,interval)
                        VALUES(?,?,?,?,?,?)""",
                (video_id, source.name, ".mp4", media["sha256"], source.stat().st_size, 3),
            )
        started = time.perf_counter()
        worker._index(video_id, threading.Event())
        item = store.video(video_id)
        if item["status"] != "ready":
            raise RuntimeError(item["error"])
        indexes.append(
            {
                "video": video_id,
                "frames": item["progress"],
                "duration_seconds": item["duration"],
                "index_seconds_model_already_loaded": time.perf_counter() - started,
            }
        )
        print(
            f"Indexed {video_id}: {item['progress']} frames in {indexes[-1]['index_seconds_model_already_loaded']:.2f}s",
            flush=True,
        )
    outcomes, latencies = [], []
    for case in annotation["cases"]:
        for lang in ["en", "tr"]:
            response = api.search(case[lang], None, 12, "SearchQuery")

            def relevant(hit):
                return hit["video_id"] == case["video"] and any(
                    start <= hit["timestamp"] <= end for start, end in case["windows"]
                )

            first_rank = next(
                (i + 1 for i, hit in enumerate(response["results"]) if relevant(hit)), None
            )
            latencies.append(response["elapsed_ms"])
            outcomes.append(
                {
                    "id": case["id"],
                    "language": lang,
                    "query": case[lang],
                    "first_relevant_rank": first_rank,
                    "results": response["results"],
                }
            )
    # Additional repetitions are for latency only, not additional independent quality examples.
    for _ in range(args.repeats - 1):
        for case in annotation["cases"]:
            for lang in ["en", "tr"]:
                latencies.append(api.search(case[lang], None, 12, "SearchQuery")["elapsed_ms"])

    def metrics(items):
        return {
            "queries": len(items),
            "hit_at_1": float(np.mean([x["first_relevant_rank"] == 1 for x in items])),
            "hit_at_5": float(
                np.mean(
                    [
                        x["first_relevant_rank"] is not None and x["first_relevant_rank"] <= 5
                        for x in items
                    ]
                )
            ),
            "mrr_at_12": float(
                np.mean(
                    [1 / x["first_relevant_rank"] if x["first_relevant_rank"] else 0 for x in items]
                )
            ),
        }

    report = {
        "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_revision": MODEL_REVISION,
        "annotation_sha256": hashlib.sha256(annotation_bytes).hexdigest(),
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "device": encoder.device,
            "gpu": torch.cuda.get_device_name(0) if args.device == "cuda" else None,
            "batch_size": args.batch_size,
            "logical_cpus": os.cpu_count(),
        },
        "media": media_manifest,
        "indexes": indexes,
        "cold_query_ms_cached_weights": cold_query_ms,
        "cached_model_load_seconds": encoder.load_seconds,
        "warm_latency_ms": {
            "samples": len(latencies),
            "p50": float(np.median(latencies)),
            "p95": float(np.percentile(latencies, 95)),
        },
        "process_rss_mib_after_run": psutil.Process().memory_info().rss / 1024**2,
        "cuda_peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2
        if args.device == "cuda"
        else None,
        "quality": {
            "all": metrics(outcomes),
            "en": metrics([x for x in outcomes if x["language"] == "en"]),
            "tr": metrics([x for x in outcomes if x["language"] == "tr"]),
        },
        "outcomes": outcomes,
        "limitations": [
            "Small development set: three animated film excerpts, 55 sampled frames.",
            "18 paired scene descriptions (36 language queries); not independent translations.",
            "Single annotator, sampled-frame relevance; no human adjudication or blind held-out set.",
            "Timing excludes download, HTTP transport and browser rendering.",
            "Warm query latency measured without concurrent indexing; p95 is a sample percentile.",
        ],
    }
    destination = ROOT / f"results-{args.device}-b{args.batch_size}.json"
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(destination),
                "quality": report["quality"],
                "warm_latency_ms": report["warm_latency_ms"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
