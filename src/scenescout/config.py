"""Small, explicit configuration surface. No cloud credentials required."""

import os
from pathlib import Path

MODEL_ID = "google/embeddinggemma-2"
MODEL_REVISION = "914f7f89142e33e77833254d9c9b90c3cef7303b"
DATA_DIR = Path(os.getenv("SCENESCOUT_DATA_DIR", ".data")).resolve()
# Download metadata only; do not emit model-library telemetry.
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
MAX_UPLOAD_BYTES = 512 * 1024 * 1024
MAX_FRAMES = 2000
MAX_DURATION_SECONDS = 7200
STATIC_DIR = Path(__file__).parent / "static"
