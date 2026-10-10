"""Run with `uv run scenescout` or `python -m scenescout`."""

import argparse
import json
import os
import socket
import threading
import time
import urllib.request
import webbrowser

import uvicorn


def main(argv=None):
    parser = argparse.ArgumentParser(description="SceneScout local video search")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--open-browser", action="store_true", help="Open the UI after the server is ready"
    )
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--batch-size", type=int, choices=range(1, 17), default=2)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    os.environ["SCENESCOUT_DEVICE"] = args.device
    os.environ["SCENESCOUT_BATCH_SIZE"] = str(args.batch_size)
    url = f"http://127.0.0.1:{args.port}"
    with socket.socket() as probe:
        probe.settimeout(0.3)
        occupied = probe.connect_ex(("127.0.0.1", args.port)) == 0
    if occupied:
        try:
            with urllib.request.urlopen(url + "/api/status", timeout=2) as response:
                status = json.load(response)
            if (
                status.get("mode") != "visual_frames"
                or status.get("model", {}).get("model") != "google/embeddinggemma-2"
            ):
                raise ValueError("Another application owns this port")
        except (OSError, ValueError):
            parser.error("Port is in use by another application. Choose a different --port.")
        if args.open_browser:
            webbrowser.open(url)
        print(f"SceneScout is already running at {url}")
        return
    if args.open_browser:

        def open_when_ready():
            url = f"http://127.0.0.1:{args.port}"
            for _ in range(100):
                try:
                    urllib.request.urlopen(url + "/api/status", timeout=1).close()
                    webbrowser.open(url)
                    return
                except OSError:
                    time.sleep(0.3)

        threading.Thread(target=open_when_ready, daemon=True).start()
    uvicorn.run(
        "scenescout.api:app",
        host="127.0.0.1",
        port=args.port,
        access_log=False,
        timeout_graceful_shutdown=10,
    )


if __name__ == "__main__":
    main()
