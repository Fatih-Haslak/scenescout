"""Build a Windows distribution with verified official uv and Deno runtimes."""

import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIMES = {
    "uv": (
        "https://github.com/astral-sh/uv/releases/download/0.13.0/uv-x86_64-pc-windows-msvc.zip",
        "088962f9e7b7bd9ea740c04c650b2a21c8928c345bd99ac24350dc924dba656c",
        ("uv.exe",),
    ),
    "deno": (
        "https://github.com/denoland/deno/releases/download/v2.9.7/deno-x86_64-pc-windows-msvc.zip",
        "a0c3101b4158d1dfb7d6a78a7bf0f3de80c96bb423c152beec8beb22786f2238",
        ("deno.exe",),
    ),
}


def stage_distribution():
    cache = ROOT / "work" / "packaging"
    cache.mkdir(parents=True, exist_ok=True)
    # A fresh stage only includes runtime files, never users' libraries or caches.
    stage = Path(tempfile.mkdtemp(prefix="windows-stage-", dir=cache)) / "SceneScout"
    stage.mkdir()
    for name in (
        "Start.cmd",
        "Start-GPU.cmd",
        "Start.ps1",
        "QUICKSTART.html",
        "LICENSE",
        "SECURITY.md",
        "pyproject.toml",
        "uv.lock",
        "README.md",
        "README.tr.md",
    ):
        shutil.copy2(ROOT / name, stage / name)
    for name in ("src/scenescout", "docs"):
        shutil.copytree(
            ROOT / name,
            stage / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "demo-*.jpg"),
        )
    (stage / "examples").mkdir()
    for name in ("ATTRIBUTION.md", "search-results.json"):
        shutil.copy2(ROOT / "examples" / name, stage / "examples" / name)
    bootstrap = stage / ".bootstrap"
    bootstrap.mkdir()
    for name, (url, digest, members) in RUNTIMES.items():
        archive = cache / f"{name}.zip"
        if not archive.exists():
            urllib.request.urlretrieve(url, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Official {name} archive checksum mismatch: {archive}")
        with zipfile.ZipFile(archive) as source:
            for member in members:
                (bootstrap / member).write_bytes(source.read(member))
    return stage


def main():
    from scenescout import __version__

    stage = stage_distribution()
    destination = ROOT / "dist" / f"SceneScout-{__version__}-Windows-x64.zip"
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                out.write(path, f"SceneScout/{path.relative_to(stage).as_posix()}")
    print(f"Built {destination} ({destination.stat().st_size / 1024**2:.1f} MiB)")
    return stage


if __name__ == "__main__":
    main()
