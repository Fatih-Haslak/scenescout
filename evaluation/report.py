"""Render published measurements without inventing scores or timings."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent


def main():
    reports = {
        device: json.loads(
            (ROOT / f"evaluation/results-{device}-b2.json").read_text(encoding="utf-8")
        )
        for device in ["cpu", "cuda"]
    }
    scaling = json.loads((ROOT / "evaluation/scaling-results.json").read_text(encoding="utf-8"))
    cpu, gpu = reports["cpu"], reports["cuda"]
    table = []
    for label, result in [("CPU / FP32", cpu), ("RTX 4060 Ti / BF16", gpu)]:
        quality = result["quality"]["all"]
        table.append(
            f"| {label} | {quality['hit_at_1']:.1%} | {quality['hit_at_5']:.1%} | {quality['mrr_at_12']:.3f} | {result['warm_latency_ms']['p50']:.0f} / {result['warm_latency_ms']['p95']:.0f} ms |"
        )
    cost_rows = []
    for label, result in [("CPU", cpu), ("GPU", gpu)]:
        total = sum(x["index_seconds_model_already_loaded"] for x in result["indexes"])
        cost_rows.append(
            f"| {label} | {result['cached_model_load_seconds']:.2f} s | {result['cold_query_ms_cached_weights'] / 1000:.2f} s | {total:.2f} s | {result['process_rss_mib_after_run']:.0f} MiB |"
        )
    scale_rows = []
    for item in scaling["synthetic_retrieval"]:
        scale_rows.append(
            f"| {item['vectors']:,} | {item['raw_matrix_mib']:.1f} MiB | {item['first_snapshot_ms']:.2f} ms | {item['warm_cached_exact_rank']['p50_ms']:.2f} / {item['warm_cached_exact_rank']['p95_ms']:.2f} ms | {item['uncached_snapshot_plus_rank']['p50_ms']:.2f} ms |"
        )
    text = f"""# SceneScout v0.2 measurements

Recorded 2026-10-10 on Windows 11, Python 3.13.9, Ryzen 5 7500F, RTX 4060 Ti 16 GB. Model revision `{cpu["model_revision"]}`. CPU PyTorch 2.14.1+cpu; CUDA PyTorch 2.14.1+cu130. Batch size 2; sampling every 3 seconds.

## Retrieval quality

Three licensed animated excerpts: *Big Buck Bunny* (60 s), *Sintel trailer* (45 s), *Elephants Dream* (60 s). **55 frames**, **18 paired scene descriptions**, **36 queries** (18 English + 18 Turkish), searched across all three videos. Contact sheets and relevance windows were fixed before model queries; query-file SHA-256 `{cpu["annotation_sha256"]}`.

Hit@k means at least one labelled relevant sampled frame appears in the first k temporally deduplicated results. MRR@12 is the mean reciprocal rank of the first relevant result (zero if absent). These metrics describe this small development set, not a general accuracy guarantee.

| Runtime | Hit@1 | Hit@5 | MRR@12 | Warm p50 / p95 |
| --- | --- | --- | --- | --- |
{chr(10).join(table)}

24/36 queries put the labelled frame first; 36/36 put it in the first five. The paired languages both achieved 12/18 first-result hits. Full rankings, including first-result misses, are committed in [CPU results](../evaluation/results-cpu-b2.json) and [CUDA results](../evaluation/results-cuda-b2.json).

![Recorded sample quality and warmed query timings](evaluation-summary.png)

## Startup and indexing cost

| Runtime | Cached model load | First text encoding including load | Index all 55 frames after model load | Process RSS after run |
| --- | --- | --- | --- | --- |
{chr(10).join(cost_rows)}

The first text encoding is measured directly through the encoder; warm timings use the application's search function (encoding + metadata lookup + exact ranking). 108 warm latency samples per mode, three repetitions of the same 36 queries. Installation, model download, HTTP transit and UI rendering are excluded. The CPU and GPU runs partially overlapped on the host, so the table is not a controlled isolated speedup comparison. RSS includes libraries/model; it is not peak memory. GPU peak allocated tensor memory: {gpu["cuda_peak_allocated_mib"]:.0f} MiB, excluding driver and other applications.

## Longer-video throughput

The full **{scaling["full_video"]["duration_seconds"]:.1f}-second** *Big Buck Bunny* film (about 10 minutes), **{scaling["full_video"]["frames"]} frames** at 3-second sampling, indexed in **{scaling["full_video"]["index_seconds_model_already_loaded"]:.2f} seconds** on CUDA after model load. This is one full-video run at the source's 320×180 resolution, not a 1080p/4K or two-hour-video benchmark. [Raw measurements](../evaluation/scaling-results.json).

## Exact scan and cache scaling

Synthetic normalized 768-dimensional vectors, seeded with `20261010`, distributed into videos of at most 2,000 frames. This isolates CPU vector-cache/ranking costs; no model or real media is encoded for this section. Cache rebuilding after a library change pays the initial snapshot cost again.

| Vectors | Raw matrix | First snapshot | Cached ranking p50 / p95 | Uncached snapshot + ranking p50 |
| --- | --- | --- | --- | --- |
{chr(10).join(scale_rows)}

Cached timings use 20 repetitions; uncached timings use five. These are sample percentiles. Query encoding is excluded. Exact scanning remains O(N × 768), with O(N log N) sorting and additional metadata memory. 50,000 vectors require ~146 MiB for the raw matrix; very large archives still need a dedicated vector index.

## Reproduce

```sh
uv sync --frozen --extra cpu --group evaluation
uv run --no-sync python examples/create_demo.py
uv run --no-sync python evaluation/prepare.py
uv run --no-sync python evaluation/run.py --device cpu --batch-size 2
# On a compatible NVIDIA machine:
uv sync --frozen --extra cuda --group evaluation
uv run --no-sync python evaluation/run.py --device cuda --batch-size 2
uv run --no-sync python evaluation/scaling.py
uv run --no-sync python evaluation/report.py
```

Each evaluation run stores its isolated library under `work/`; it does not touch your `.data` library. CPU-only machines can reproduce the CPU report and annotations; CUDA/scaling measurements require compatible hardware. Scripts fail visibly on inference/decode errors. No fallback vectors or prewritten search responses are used in the evaluation.

## Scope of evidence

The annotations were made by Codex from visible contact sheets, with no human adjudication. This is a public development set of animation, with paired translations rather than 36 independent scenes. There is no blind held-out test set, live-action footage, negative-query rejection metric, concurrency latency benchmark or claim about audio/motion understanding. Small windows sometimes make visually related shots count as misses; the raw rankings preserve those cases.

Inspect [queries and relevance windows](../evaluation/queries.json), [media hashes](../evaluation/media-manifest.json), and [media licences](../evaluation/ATTRIBUTION.md). Contact sheets: [Bunny](evaluation-bunny.jpg), [Sintel](evaluation-sintel.jpg), [Dream](evaluation-dream.jpg). Historical v0.1 observations remain in [performance.md](performance.md).
"""
    (ROOT / "docs/evaluation.md").write_text(text, encoding="utf-8")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    fig.patch.set_facecolor("#f4f7fc")
    for ax in axes:
        ax.set_facecolor("#f4f7fc")
        ax.spines[["top", "right"]].set_visible(False)
    quality = cpu["quality"]["all"]
    values = [quality["hit_at_1"] * 100, quality["hit_at_5"] * 100]
    bars = axes[0].bar(["Hit@1", "Hit@5"], values, color=["#4263eb", "#15aabf"], width=0.55)
    axes[0].bar_label(bars, labels=["24 / 36", "36 / 36"], padding=5)
    axes[0].set_ylim(0, 115)
    axes[0].set_ylabel("Queries with a relevant scene (%)")
    axes[0].set_title("Small development set · 55 frames")
    medians = [cpu["warm_latency_ms"]["p50"], gpu["warm_latency_ms"]["p50"]]
    p95 = [cpu["warm_latency_ms"]["p95"], gpu["warm_latency_ms"]["p95"]]
    axes[1].bar([0, 1], medians, width=0.35, label="p50", color="#4263eb")
    axes[1].bar([0.38, 1.38], p95, width=0.35, label="p95", color="#15aabf")
    axes[1].set_xticks([0.19, 1.19], ["CPU FP32", "RTX 4060 Ti BF16"])
    axes[1].set_ylabel("Server search function (ms)")
    axes[1].set_title("Warm text queries · 108 samples / mode")
    axes[1].legend(frameon=False)
    fig.suptitle("SceneScout · recorded local inference", fontsize=16, fontweight="bold")
    fig.savefig(ROOT / "docs/evaluation-summary.png", dpi=160)
    plt.close(fig)
    print("Updated docs/evaluation.md and measured chart.")


if __name__ == "__main__":
    main()
