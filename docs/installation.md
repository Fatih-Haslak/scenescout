# Install SceneScout

[Türkçe kurulum rehberi](installation.tr.md)

## Windows: recommended installer

**[Download SceneScout Setup for Windows x64](https://github.com/Fatih-Haslak/scenescout/releases/latest/download/SceneScout-Setup-Windows-x64.exe)**. Open it, choose English or Turkish, and finish the wizard. Double-click the **SceneScout** desktop shortcut. No administrator privileges, manual Python installation or API key are needed. Windows 10/11 x64 is supported.

| Stage | What happens |
| --- | --- |
| Installer | Copies the app and guide, creates shortcuts and an uninstaller. |
| First launch | Downloads compatible Python and locked dependencies automatically. |
| First video | Downloads approximately 1.5 GB of model weights, then indexes frames. |
| Later use | Reuses the environment and cached model. |

First use requires internet, several GB of free disk space and sufficient RAM. Duration depends on hardware and connection speed. CPU works but indexing is slower. Keep the launch window open while using the app; stop with **Ctrl+C**. Closing the browser tab does not stop the server. Search after the video says **Ready**.

The Start menu includes the bilingual offline **Getting started** guide. CPU is the default. The optional **NVIDIA GPU** shortcut installs CUDA 13.0 PyTorch for a compatible GPU/driver. Its packages are larger; CPU and GPU environments are separate.

The installer is unsigned, so Windows may show a publisher warning. Use the official release and compare `SHA256SUMS.txt`. No security settings or global Python installations are modified. This is an online first-use installer, not a fully offline inference bundle.

## Data, upgrades and uninstall

| Files | Default location |
| --- | --- |
| App | `%LOCALAPPDATA%\Programs\SceneScout` |
| Video copies and indexes | `%LOCALAPPDATA%\SceneScout\Data` |
| Python and CPU/GPU environments | `%LOCALAPPDATA%\SceneScout\Runtime` and `Environments` |
| Setup logs | `%LOCALAPPDATA%\SceneScout\Logs\setup-cpu.log` / `setup-cuda.log` |
| Model and package caches | Hugging Face and uv's user cache locations |

Stop with Ctrl+C before running a newer installer. Updates preserve the separate library. Uninstall through **Windows Settings → Apps**. Uninstall preserves data and downloaded environments; back up and remove those folders yourself if you want to erase them permanently.

Existing ZIP/source libraries are not automatically migrated. Stop the old app and copy the **contents** of its `.data` into `%LOCALAPPDATA%\SceneScout\Data` before the new app's first launch. Do not overwrite an existing library; back it up first.

## Troubleshooting

- **Incomplete download:** check internet/disk space, then launch again. Completed cache downloads are reused; the setup log records errors.
- **Browser did not open:** check the launch window. If the server is ready, open [the local app](http://127.0.0.1:8765).
- **Port in use:** stop the other SceneScout instance. Advanced usage can select another port with `Start.ps1 -Port 8877`.
- **GPU failed:** use CPU and check NVIDIA driver compatibility.
- **Video link failed:** only single public videos are supported; private, login-required, live or platform-blocked content may fail. Upload a local copy instead.

Include the version and error when reporting a problem. Remove personal paths, video URLs and private information from logs before sharing them.

## Portable ZIP

Download `SceneScout-0.4.0-Windows-x64.zip` from [the release](https://github.com/Fatih-Haslak/scenescout/releases/latest). **Extract first**, open `QUICKSTART.html`, then double-click `Start.cmd`. Do not launch files directly inside the archive preview. This option does not create shortcuts or an uninstall entry.

The ZIP stores its library in `.data` inside the extracted folder. Preserve that directory when upgrading. CPU/GPU environments use `.venv-cpu` and `.venv-cuda`. Model and package caches remain in their libraries' user cache directories.

## Source installation / advanced usage

Use Python 3.12/3.13 and [uv](https://docs.astral.sh/uv/getting-started/installation/):

```sh
git clone https://github.com/Fatih-Haslak/scenescout.git
cd scenescout
uv run --frozen --extra cpu scenescout --open-browser
```

On Windows, `Start.cmd` also prepares the environment. From source it downloads checksum-verified official uv and Deno if missing. Existing PowerShell execution policies are not changed; the launcher enables the project's script for that invocation only. Review [Start.ps1](../Start.ps1).

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start.ps1 -SetupOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start.ps1 -Port 8877
```

macOS/Linux use the source workflow. For YouTube install [Deno](https://docs.deno.com/runtime/getting_started/installation/) or provide Node 22+. The Python dependencies include yt-dlp, its EJS helper and imageio-ffmpeg. FFmpeg enables conversion/playback; visual search does not index audio.

For isolated installer troubleshooting, `SCENESCOUT_HOME` overrides the installed data/runtime root. Source/ZIP users can configure `SCENESCOUT_DATA_DIR` and `UV_PROJECT_ENVIRONMENT` directly. Stop other copies before changing libraries.

## Build and integrity

```powershell
uv run --frozen --extra cpu python scripts/build_windows.py
uv run --frozen --extra cpu python scripts/build_installer.py --iscc "C:\path\to\ISCC.exe"
```

The EXE requires the official **Inno Setup 7** compiler; the release was built with 7.1.0. The compiler is a build tool, not part of the distributed app. It supports portable mode so it can be kept in a build folder without a system installation. [Official download and verification](https://jrsoftware.org/isdl-verify.php).

The packager uses an explicit runtime file list. User media, model weights, caches, virtual environments and build tools are excluded. It bundles official uv 0.13.0 and Deno 2.9.7 only after verifying pinned archive SHA-256 hashes; those pins are visible in [build_windows.py](../scripts/build_windows.py). No Git checkout is needed to build from an extracted source archive. Release checksums cover the EXE, ZIP, wheel and source archive.

Bundled uv is © Astral Software Inc., dual licensed MIT/Apache-2.0. Deno is © the Deno authors, MIT licensed. Licence copies ship in `docs/vendor/`. [uv source](https://github.com/astral-sh/uv/tree/0.13.0), [Deno source](https://github.com/denoland/deno/tree/v2.9.7).
