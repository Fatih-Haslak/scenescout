# SceneScout v0.3.1

YouTube downloads could fail with HTTP 403 and searches always returned nearest frames, even for unrelated queries. This release adds a bounded public HLS fallback and a user-selected minimum similarity filter for text and reference-image search.

- A YouTube 403 gets one fresh HLS attempt; partial files are cleared and existing size/duration/cancellation limits remain. Unrelated errors are not automatically retried.
- Audio and video streams share one size/progress budget. Progress writes retry brief Windows file locks; local filesystem errors receive a separate message and a safe diagnostic type.
- Search scores are filtered before rounding. No qualifying frames produces an explicit message. Thresholds are not confidence percentages or a calibrated scene-presence detector; the default preserves nearest-frame ranking.
- Manual library refreshes reuse a single polling loop.
- 74 behavioral tests passed locally with 88.07% line coverage, plus formatting, syntax and distribution checks. CI tests use model/downloader doubles; public-network and real-model checks are separate.

Actual integration checks: a public YouTube HLS download and an automatic 403 fallback completed. With the supported Deno runtime, the previously failed browser import finished download/conversion and indexed a 596-second video into 199 frames. Turkish search and 720p playback worked. Three unrelated descriptions against the existing X video scored below 0.60; the 0.70 filter returned no hits, including in the browser. These small observations are not general platform availability or accuracy claims.

Speech search, summaries, clip export and a large-archive vector index remain outside this release. Existing labelled retrieval results are unchanged: 24/36 first-result hits on a small development set.

Windows: extract the starter ZIP and run `Start.cmd` (CPU) or `Start-GPU.cmd` (CUDA). Python, locked dependencies and the official Deno runtime are prepared automatically. Model weights download on first use. SHA-256 checksums accompany the release assets.
