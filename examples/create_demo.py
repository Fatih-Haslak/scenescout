"""Download Blender's CC BY 3.0 film and make a 30-second silent demo excerpt.

Run: uv run --with imageio-ffmpeg python examples/create_demo.py
Media is never downloaded by the application itself.
"""

import subprocess
import shutil
import urllib.request
import zipfile
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
URL = "https://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4.zip"


def main():
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    original = cache / "big-buck-bunny.mp4"
    if not original.exists():
        print("Downloading Big Buck Bunny from Blender Foundation (CC BY 3.0)…")
        archive = cache / "big-buck-bunny.zip"
        partial = archive.with_suffix(".part")
        request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target)
        partial.replace(archive)
        with zipfile.ZipFile(archive) as bundle:
            name = next(name for name in bundle.namelist() if name.lower().endswith(".mp4"))
            with bundle.open(name) as source, original.open("wb") as target:
                shutil.copyfileobj(source, target)
    target = ROOT / "demo.mp4"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            "30",
            "-i",
            str(original),
            "-t",
            "30",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(target),
        ],
        check=True,
    )
    print(f"Created {target}")
    print("Excerpt of Big Buck Bunny © 2008 Blender Foundation / www.bigbuckbunny.org")
    print("CC BY 3.0: https://creativecommons.org/licenses/by/3.0/")
    print("Changes: excerpt from 00:30 to 01:00, audio removed, H.264 re-encoded.")


if __name__ == "__main__":
    main()
