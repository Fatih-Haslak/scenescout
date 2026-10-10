# Recorded demo observations

Historical **v0.1** observations. See the [v0.2 evaluation](evaluation.md) for labelled retrieval metrics, actual CUDA execution, longer-video throughput and synthetic cache scaling.

Recorded on **2026-10-10** with actual local inference. Small-sample observations, not broad quality or throughput claims.

| Setting | Value |
| --- | --- |
| Runtime | Windows, Python 3.13.9, PyTorch 2.14.1, CPU |
| Processor | AMD Ryzen 5 7500F, 6 cores |
| Model | `google/embeddinggemma-2` |
| Model revision | `914f7f89142e33e77833254d9c9b90c3cef7303b` |
| Media | 30-second Big Buck Bunny excerpt, 320×180, silent H.264 MP4 |
| Sampling | Every 3 seconds, 10 frames |
| Cached model load | 21.95 seconds |
| Indexing, including cached model load | 59.59 seconds |

| Query | Server latency | First timecode | Cosine similarity |
| --- | --- | --- | --- |
| A rabbit sitting in the grass | 58 ms | 00:18 | 0.7284 |
| A dark cave inside a tree | 66 ms | 00:00 | 0.7463 |
| Çimenlerde oturan bir tavşan | 61 ms | 00:18 | 0.7294 |
| Reference image: JPEG thumbnail of the rabbit frame | 3,787 ms | 00:18 | 0.9887 |

Search latency includes query encoding, scoring and shortlist generation. It excludes HTTP transit, UI rendering, installation and model download. Indexing costs substantially more than a warmed text query.

The rabbit scene is visible at the selected timecode. The tree query retrieves a related opening shot. There is no annotated ground truth, recall measurement or representative evaluation set. Do not infer p95 latency, recall, GPU speed or hardware-independent performance from these examples.

Reproduce media preparation with `examples/create_demo.py`. See `examples/search-results.json` for an actual exported response and `examples/ATTRIBUTION.md` for licensing. GPU hardware was not used.
