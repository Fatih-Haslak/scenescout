"""Build a starter ZIP with a pinned, checksum-verified official uv runtime."""

import hashlib
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UV_VERSION = "0.13.0"
UV_SHA256 = "088962f9e7b7bd9ea740c04c650b2a21c8928c345bd99ac24350dc924dba656c"


def main():
    cache = ROOT / "work" / "packaging"
    cache.mkdir(parents=True, exist_ok=True)
    runtime = cache / "uv.zip"
    if not runtime.exists():
        urllib.request.urlretrieve(
            f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-pc-windows-msvc.zip",
            runtime,
        )
    if hashlib.sha256(runtime.read_bytes()).hexdigest() != UV_SHA256:
        raise RuntimeError("Official uv archive checksum mismatch")
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    files += (
        subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT
        )
        .decode()
        .split("\0")
    )
    destination = ROOT / "dist" / "SceneScout-0.2.0-Windows-x64.zip"
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name in sorted(set(files)):
            if name and (ROOT / name).is_file():
                out.write(ROOT / name, f"SceneScout/{name}")
        with zipfile.ZipFile(runtime) as source:
            for name in source.namelist():
                if name in {"uv.exe", "uvw.exe", "uvx.exe"}:
                    out.writestr(f"SceneScout/.bootstrap/{name}", source.read(name))
    print(f"Built {destination} ({destination.stat().st_size / 1024**2:.1f} MiB)")


if __name__ == "__main__":
    main()
