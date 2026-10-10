# Architecture and decisions

SceneScout is a single-user loopback HTTP server with a static browser UI. Its default inference path is local.

| Module | Responsibility |
| --- | --- |
| `api.py` | Validation, streamed upload, library, search and media endpoints |
| `encoder.py` | Lazy model load, pinned revision, serialized inference, dtype and vector checks |
| `indexer.py` | Single background worker, batch frame sampling, checkpoints, resume and cancellation |
| `retrieval.py` | Exact cosine ranking, temporal diversity and generation-based vector cache |
| `store.py` | SQLite lifecycle, connection ownership and metadata |
| `config.py` | Paths, model identity and resource limits |
| `static/` | Bilingual UI, playback, filmstrip and exports |

## Import lifecycle

Uploads stream to server-generated filenames while computing SHA-256. Content hashes deduplicate imports. Display names never determine storage paths.

OpenCV reads duration and samples one image per interval. The worker bounds image dimensions and encodes small batches (default 2). Thumbnail files are written before vectors and progress commit together in one transaction. Resume skips committed frames with existing thumbnails and repairs missing thumbnails by re-encoding the affected frame. A crash can discard the in-flight batch; already committed frames survive.

Search includes only `ready` videos. Scenes persist incrementally; the final status publishes the index after all frames are stored. Incomplete indexes remain invisible to retrieval.

Removal persists a `removing` tombstone before signalling a running job. Its worker cleans up after the current batch; metadata is deleted after files. Restart completes interrupted removals. Locked files preserve the tombstone and expose a retryable error without preventing the rest of the library from opening. Graceful shutdown also handles cancelled queued futures, which never enter worker cleanup. Interrupted queued/indexing jobs become `paused`; the user resumes from saved frames via the UI or `POST /api/videos/{id}/resume`.

Each operation owns a SQLite connection and explicitly closes it in `finally` after commit/rollback. WAL allows reads alongside indexing writes. Scene deletion cascades through a foreign key. Vectors are little-endian float32 blobs, without pickle.

## Retrieval and scaling

Text uses `SearchQuery`; reference images use the vision encoder. Cosine similarity scores both against the same frame vectors. Hits within twice the sampling interval are deduplicated per video.

The exact cosine scan costs O(N × 768) work, with O(N log N) stable score sorting. A library-generation cache reuses metadata and the dense vector matrix across queries. Publish/removal/status transitions invalidate it; incomplete frames are never cached. Queries take the snapshot after inference to avoid returning a video removed while query encoding was waiting. The UI also discards responses belonging to a search started before a removal action. The cache is process-local: one application process owns one library. External database writers/multiple servers sharing a data directory are unsupported. A dedicated vector index remains a future scaling change. Scores are not confidence guarantees; unrelated queries still return nearest neighbors.

Only image frames carry visual information. This release does not use native video-sequence or audio encoding and cannot reliably infer motion solely from temporal relationships.

## Model lifecycle

The model loads lazily. A lock serializes initialization and inference, preventing duplicate loads and overlapping device-memory spikes. Queries can wait behind a frame being encoded.

The audio tower is disabled. CPU uses float32, compatible CUDA uses bfloat16; CUDA falls back to float32 if BF16 is unsupported. Shape, finite-value and nonzero-norm checks reject invalid outputs before persistence. CPU and CUDA 13.0 installation variants are separately locked. Explicitly requesting an unavailable CUDA device fails rather than silently switching. The app never substitutes mock embeddings or a remote inference service.

`uv.lock` captures dependencies and the model commit is pinned independently. Cached weights allow offline loading. `HF_HUB_OFFLINE=1` prevents model-download attempts.

## UI and boundaries

Static assets ship in the Python wheel, without a frontend build step. User names and queries use text nodes. Polling exposes job progress; HTTP range requests support playback seeking.

Search scope and current preview are independent. A library-wide query can preview any video; selecting a library item narrows subsequent searches. JSON exports include query, model, scores, timecodes and server latency.

Offline HTML docs and an OpenAPI schema expose the API. Browser cross-origin requests and unexpected hosts are rejected. This is a local application, without multi-user authentication. See `SECURITY.md`.

## Observed release scope

Source lint/format, Python compilation, JavaScript syntax and distribution packaging are checked. The app walkthrough used a real model and licensed video for import, indexing, English/Turkish search, image search, timecode seeking and export. Screenshots are from the running app.

40 automated behavioral tests cover persistence, restart/removal recovery, resume checkpoints, invalid uploads, duplicates, local boundaries, model failures, stale search results, ranking, cache invalidation, launch behavior and dtype safety. Model tests use explicit doubles; they do not prove real-model quality. Separate real CPU/CUDA inference measurements, labelled development queries, a full-film index and synthetic vector scaling are documented in [evaluation.md](evaluation.md). Hosted CI covers Windows/Linux and Python 3.12/3.13. macOS real inference remains unverified.
