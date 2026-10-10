# SceneScout v0.1.0

Find a remembered visual moment in a local video, using text or a reference image.

- Real EmbeddingGemma 2 inference, pinned to a model revision.
- Local video import, background frame indexing and content deduplication.
- Ranked scenes with seek-to-timecode playback and an interactive filmstrip.
- English/Turkish interface and queries, JSON result export and local API docs.
- Windows launcher, reproducible dependency lock, MIT source and licensed demo preparation.

Recorded demo: 30 seconds, 10 sampled frames, Windows CPU inference. Warmed English/Turkish text searches took 58–66 ms in this small example; image-query search took 3.8 seconds. These are demonstration measurements, not general performance guarantees.

Current scope is visual frame retrieval. Audio, motion analysis, clip export, macOS/Linux execution and GPU performance are outside the verified scope. No automated behavioral test suite is included.

Install from source using the README. The wheel is an alternative Python distribution, not a standalone Windows executable. Model weights download separately on first use.
