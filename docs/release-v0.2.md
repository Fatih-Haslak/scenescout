# SceneScout v0.2.0 — Resume, measured retrieval, and easy Windows setup

Interrupted imports retain committed frames and can resume from the library. SQLite connections close explicitly; batch checkpoints commit scenes and progress atomically. Persisted removal tombstones finish cleanup after restart. Search reads its library snapshot after inference, and the UI discards responses made stale by a removal.

This release adds 40 behavioral tests, a Windows/Linux × Python 3.12/3.13 CI matrix, locked CPU/CUDA installation choices, validated batch embeddings and a vector cache. Tests enforce at least 80% line coverage; observed local coverage was 89.1%.

Real EmbeddingGemma 2 inference was measured on CPU and RTX 4060 Ti. A small development set of three licensed animated excerpts (55 frames, 36 EN/TR queries) yielded Hit@1 66.7% and Hit@5 100%. Warm text-query p50/p95: CPU 66/73 ms, GPU 32/34 ms. These are sample results, not a general accuracy guarantee. Raw rankings include misses; annotation hashes, media hashes and reproduction scripts are published. The evaluation documents startup cost, one full-film index and synthetic vector-cache scaling separately.

## Download

- `SceneScout-0.2.0-Windows-x64.zip`: extract and double-click `Start.cmd`. Python/uv need not be installed manually. `Start-GPU.cmd` selects supported NVIDIA CUDA hardware. First setup/inference downloads dependencies and model weights; later use reuses caches.
- Python wheel and source archive for developers.
- `SHA256SUMS.txt` for artifact integrity.

The Windows ZIP includes a checksum-verified official uv runtime and licence notices; it is not an offline model bundle or signed MSI. Videos and model weights are not included. Retain `.data` when upgrading. [Installation guide](https://github.com/Fatih-Haslak/scenescout/blob/main/docs/installation.md), [evaluation and limits](https://github.com/Fatih-Haslak/scenescout/blob/main/docs/evaluation.md).

Visual-frame search remains the product scope; audio, transcripts and motion recognition are not included. macOS real inference remains unverified.
