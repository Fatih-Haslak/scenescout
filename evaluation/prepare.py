"""Prepare licensed, fixed excerpts and contact sheets before annotating queries."""

import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

import cv2
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCES = [
    {
        "id": "bunny",
        "name": "Big Buck Bunny",
        "start": 30,
        "seconds": 60,
        "local": "examples/.cache/big-buck-bunny.mp4",
        "url": None,
    },
    {
        "id": "sintel",
        "name": "Sintel trailer",
        "start": 0,
        "seconds": 45,
        "url": "https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4",
    },
    {
        "id": "dream",
        "name": "Elephants Dream",
        "start": 30,
        "seconds": 60,
        "url": "https://download.blender.org/ED/elephantsdream-480-h264-st-aac.mov",
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contact-only", action="store_true")
    args = parser.parse_args()
    media = ROOT / "media"
    media.mkdir(exist_ok=True)
    manifest = []
    for source in SOURCES:
        target = media / f"{source['id']}.mp4"
        original = (
            ROOT.parent / source["local"]
            if source.get("local")
            else media / f"{source['id']}-original{Path(source['url']).suffix}"
        )
        if not args.contact_only and not target.exists():
            if not original.exists():
                if not source["url"]:
                    raise SystemExit("Run examples/create_demo.py first to cache Big Buck Bunny.")
                print(f"Downloading {source['name']} from Blender Foundation", flush=True)
                request = urllib.request.Request(
                    source["url"], headers={"User-Agent": "Mozilla/5.0"}
                )
                partial = original.with_suffix(".part")
                with (
                    urllib.request.urlopen(request, timeout=60) as response,
                    partial.open("wb") as out,
                ):
                    shutil.copyfileobj(response, out)
                partial.replace(original)
            subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    str(source["start"]),
                    "-i",
                    str(original),
                    "-t",
                    str(source["seconds"]),
                    "-an",
                    "-vf",
                    "scale=480:-2",
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
        cap = cv2.VideoCapture(str(target))
        duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        times = list(range(0, int(duration), 3))
        sheet = Image.new("RGB", (1100, 36 + ((len(times) + 4) // 5) * 154), "#101923")
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default(size=16)
        draw.text(
            (12, 8), f"{source['name']} · clip-relative timecodes · sampled every 3s", font=font
        )
        for i, timestamp in enumerate(times):
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f"Cannot read {target} at {timestamp}s")
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            image.thumbnail((212, 122))
            x, y = (i % 5) * 220 + 4, 36 + (i // 5) * 154
            sheet.paste(image, (x, y))
            draw.text((x, y + 124), f"{timestamp:02d}s", font=font)
        cap.release()
        sheet.save(ROOT.parent / "docs" / f"evaluation-{source['id']}.jpg", quality=90)
        manifest.append(
            {
                "id": source["id"],
                "name": source["name"],
                "clip_start": source["start"],
                "duration": duration,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        )
    (ROOT / "media-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Prepared 3 excerpts. Annotate queries from contact sheets before running retrieval.")


if __name__ == "__main__":
    main()
