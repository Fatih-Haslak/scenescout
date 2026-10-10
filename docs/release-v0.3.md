# SceneScout v0.3.0

Paste a public YouTube/Shorts or X/Twitter video link and search its scenes on your own device. Downloads run in the background, show progress, can be cancelled/retried, and are converted to H.264 MP4 before joining the existing frame index. Source links are preserved in the library and exported search results.

- Windows launcher installs checksum-verified official Deno for YouTube extraction, alongside managed Python and locked dependencies.
- Only fixed platform extractors; no generic URL fetching, browser cookies or user plugins. Live, private and sign-in-only content is unsupported. Public platform availability can change.
- 66 automated behavioral tests; actual ffmpeg conversion and deterministic cancellation/timeout checks. CI covers Windows/Linux and Python 3.12/3.13. X import, conversion, playback and real-model scene search passed outside CI. YouTube downloaded once, but repeat attempts returned HTTP 403; repeated availability is not guaranteed on this network.
- Existing library data migrates in place. Preserve `.data` when upgrading. Download retry starts again; already indexed frames retain their resume behavior.

Download the Windows starter ZIP, extract into a writable folder and double-click **Start.cmd**, or **Start-GPU.cmd** for compatible NVIDIA CUDA. First use needs internet. The wheel/source archives are for source installations. SHA256SUMS.txt covers all assets.

SceneScout uses Google EmbeddingGemma 2 image/text embeddings with local cosine retrieval. This release searches sampled visual frames; it does not transcribe speech, generate summaries or process whole video sequences. [Limits and real link examples](https://github.com/Fatih-Haslak/scenescout/blob/main/docs/link-imports.md).
