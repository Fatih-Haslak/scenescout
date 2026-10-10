# Windows starter package

Download `SceneScout-0.3.0-Windows-x64.zip` from [the release](https://github.com/Fatih-Haslak/scenescout/releases/tag/v0.3.0), extract into a writable folder, and double-click `Start.cmd`.
Python and uv do not need to be installed manually. The ZIP bundles official uv 0.13.0; uv downloads a compatible Python if needed and installs locked dependencies. The model downloads on first inference. First use needs internet and several GB of free space. Later launches reuse the environment and cached model.

`Start.cmd` selects CPU. `Start-GPU.cmd` selects CUDA 13.0 PyTorch on a supported NVIDIA GPU/driver. Both use the same `.venv`; switching changes the PyTorch variant. GPU packages are significantly larger. No administrator access, registry changes or global Python changes are needed. Package and model caches use their libraries' cache directories outside the application folder.

This is an x64 Windows starter ZIP, not a signed MSI, fully offline bundle or single-file inference executable. Stop the app with Ctrl+C in its terminal. Copies and indexes live in `.data`; preserve that directory when upgrading. Model weights are downloaded separately.

From source, `Start.cmd` downloads the same official uv ZIP and checks its pinned SHA-256 before extraction. Existing execution policies are not changed; the launcher enables this repository's script for that invocation only. Review [Start.ps1](../Start.ps1) for all steps.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start.ps1 -SetupOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start.ps1 -Port 8877
```

macOS/Linux retain the source workflow: `uv run --frozen --extra cpu scenescout --open-browser`.

YouTube links require a supported JavaScript runtime. Windows launchers download official Deno 2.9.7 into `.bootstrap`, verify ZIP SHA-256 `a0c3101b4158d1dfb7d6a78a7bf0f3de80c96bb423c152beec8beb22786f2238`, then reuse it on later launches. Deno is not bundled inside the starter ZIP. On other platforms install [Deno](https://docs.deno.com/runtime/getting_started/installation/) or provide Node 22+. yt-dlp and its packaged EJS helper, plus the imageio-ffmpeg media runtime, are locked Python dependencies. FFmpeg enables conversion and browser playback; visual search does not index its audio.

## Build and integrity

```sh
uv run --frozen --extra cpu python scripts/build_windows.py
```

The packager verifies the official uv archive hash and packages Git-tracked/non-ignored files; imported media, model weights, caches and virtual environments are excluded. Release checksums cover all downloadable artifacts.

Bundled uv is © Astral Software Inc., dual licensed MIT/Apache-2.0. [Upstream source](https://github.com/astral-sh/uv/tree/0.13.0); copies of both licences are in `docs/vendor/`.
