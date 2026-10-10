"""Run with `uv run scenescout` or `python -m scenescout`."""

import argparse
import threading
import time
import urllib.request
import webbrowser

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="SceneScout local video search")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--open-browser", action="store_true", help="Open the UI after the server is ready"
    )
    args = parser.parse_args()
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
    uvicorn.run("scenescout.api:app", host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
