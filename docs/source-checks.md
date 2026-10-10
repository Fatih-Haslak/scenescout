# Checks and verification

v0.3 includes 66 automated behavioral tests, 88.3% observed line coverage on Windows Python 3.13.9, and a CI coverage floor of 80%. Coverage measures exercised lines, not model quality or correctness guarantees. Tests use isolated temporary libraries; they do not modify the user's `.data`. They cover link canonicalization and rejected hosts/credentials, download queue limits, actual ffmpeg conversion, subprocess cancellation/timeout, retry/removal recovery, connection closure/rollback, atomic checkpoints, resume without repeating committed frames, corrupt media, duplicate/invalid uploads, local request guards, inference failures, stale deletion/search results, temporal diversity, cache invalidation, launch options and BF16/FP32 selection.

```sh
uv sync --frozen --extra cpu --group dev
uv run --no-sync pytest --cov=scenescout --cov-report=term-missing --cov-fail-under=80
uv run --no-sync ruff check src examples scripts evaluation tests
uv run --no-sync ruff format --check src examples scripts evaluation tests
uv run --no-sync python -m compileall -q src examples scripts evaluation
node --check src/scenescout/static/app.js
npx --yes prettier@3.9.10 --check "src/scenescout/static/*.{js,css,html}"
uv build
```

The [Checks workflow](https://github.com/Fatih-Haslak/scenescout/actions/workflows/checks.yml) is configured for Windows/Linux × Python 3.12/3.13 on pushes, pull requests and manual dispatch. Each job runs locked CPU dependency installation, behavioral tests and coverage, formatting, syntax checks and distribution build. Workflow permissions are read-only; actions are pinned to immutable commit SHAs. The editable source is mirrored in `docs/ci-workflow.yml`. Check the linked run's conclusion for hosted results; a configuration file alone does not prove that CI passed.

CI avoids model downloads by using explicit test doubles for inference; small generated media still exercises actual OpenCV decoding. [Separate evaluation](evaluation.md) records real CPU/CUDA model inference, labelled queries and scaling.

The Windows starter package was extracted into a separate writable folder with only managed Python allowed. It downloaded Python 3.13.16, installed locked CPU dependencies, started the server and served its API/UI. This checks the Python bootstrap path on Windows x64, not every Windows machine or security-software configuration.

The v0.3 starter package was also extracted separately: managed Python 3.13.16 installed 65 production dependencies and the launcher downloaded official Deno 2.9.7. Its ZIP hash matched the pinned checksum and the executable reported the expected version. Real-platform observations, including YouTube repeat-download HTTP 403 and successful X import/search, are recorded in [link-imports.md](link-imports.md).

Actual browser verification also imported a full licensed film, stopped the app during indexing, reopened the library with 56/199 saved frames, clicked the resume action, and reached `ready` at 199 frames. [Paused UI evidence](resume-paused.jpg). A separate Turkish query selected the rabbit at 00:18 with real GPU inference. The paused and resumed states are backed by persisted model embeddings, not injected UI state.
