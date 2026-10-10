# SceneScout v0.3.2

Interrupted video previews could leave a shutting-down server waiting indefinitely for old HTTP connections, retaining its model in memory. The CLI now waits at most ten seconds for HTTP requests to drain, then cancels stalled requests and reaches application cleanup. Import/index workers retain their existing checkpoint and cancellation behavior; this deadline does not interrupt an in-flight model batch.

Includes v0.3.1's public HLS recovery after YouTube 403, shared stream size limits, Windows progress-file retry, optional text/image similarity filtering and a single library polling loop.

Validation: 74 behavioral tests, source formatting/syntax, distribution checks and a controlled stalled HTTP stream. That stream was canceled and lifespan cleanup completed in 10.15 seconds. Public YouTube download, conversion, 199-frame indexing, Turkish real-model search and 720p playback were checked separately.

Download the Windows starter ZIP and run `Start.cmd` (CPU) or `Start-GPU.cmd` (CUDA). Locked dependencies and the official Deno runtime are prepared automatically. SHA-256 checksums accompany all assets.

Public platform availability and semantic accuracy are not guaranteed. The similarity filter is user-selected, not calibrated confidence. Speech search, summaries, clip export and a large-archive vector index remain outside this release.
