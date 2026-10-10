# Architecture and decisions

SceneScout is a single-user loopback HTTP server with a static browser UI. Its default inference path is local.

| Module | Responsibility |
| --- | --- |
| `api.py` | Validation, streamed upload, library, search and media endpoints |
| `encoder.py` | Lazy model load, pinned revision, serialized inference, dtype and vector checks |
| `indexer.py` | Single background worker, frame sampling, progress and cancellation |
| `store.py` | SQLite lifecycle, connection ownership and metadata |
| `config.py` | Paths, model identity and resource limits |
| `static/` | Bilingual UI, playback, filmstrip and exports |

## Import lifecycle

Uploads stream to server-generated filenames while computing SHA-256. Content hashes deduplicate imports. Display names never determine storage paths.

OpenCV reads duration and samples one image per interval. The worker bounds image dimensions, encodes a normalized vector, and saves a thumbnail. Progress is committed after each frame.

Search includes only `ready` videos. Scenes persist incrementally; the final status publishes the index after all frames are stored. Incomplete indexes remain invisible to retrieval.

Removal signals a running job; its worker cleans up after the current inference. Idle-video cleanup is immediate. Graceful shutdown preserves unfinished imports with an error. Restart marks queued/indexing jobs interrupted; the user explicitly removes and re-imports them.

Each operation owns a SQLite connection. WAL allows reads alongside indexing writes. Scene deletion cascades through a foreign key. Vectors are little-endian float32 blobs, without pickle.

## Retrieval and scaling

Text uses `SearchQuery`; reference images use the vision encoder. Cosine similarity scores both against the same frame vectors. Hits within twice the sampling interval are deduplicated per video.

The exact cosine scan costs O(N × 768) work and reads all vectors into memory on each query. This makes a modest local library straightforward to inspect. A vector index is a future scaling change. Scores are not confidence guarantees; unrelated queries still return nearest neighbors.

Only image frames carry visual information. This release does not use native video-sequence or audio encoding and cannot reliably infer motion solely from temporal relationships.

## Model lifecycle

The model loads lazily. A lock serializes initialization and inference, preventing duplicate loads and overlapping device-memory spikes. Queries can wait behind a frame being encoded.

The audio tower is disabled. CPU uses float32, compatible CUDA uses bfloat16. Shape and finite-value checks reject invalid outputs before persistence. The app never substitutes mock embeddings or a remote inference service.

`uv.lock` captures dependencies and the model commit is pinned independently. Cached weights allow offline loading. `HF_HUB_OFFLINE=1` prevents model-download attempts.

## UI and boundaries

Static assets ship in the Python wheel, without a frontend build step. User names and queries use text nodes. Polling exposes job progress; HTTP range requests support playback seeking.

Search scope and current preview are independent. A library-wide query can preview any video; selecting a library item narrows subsequent searches. JSON exports include query, model, scores, timecodes and server latency.

Offline HTML docs and an OpenAPI schema expose the API. Browser cross-origin requests and unexpected hosts are rejected. This is a local application, without multi-user authentication. See `SECURITY.md`.

## Observed release scope

Source lint/format, Python compilation, JavaScript syntax and distribution packaging are checked. The app walkthrough used a real model and licensed video for import, indexing, English/Turkish search, image search, timecode seeking and export. Screenshots are from the running app.

No automated behavioral test suite or retrieval benchmark is included. macOS, Linux, CUDA execution and large-library scaling are unverified.
