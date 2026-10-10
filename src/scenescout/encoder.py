"""Lazy, serialized model loading and inference. No fake fallback embeddings."""

import threading
import time

import numpy as np

from .config import MODEL_ID, MODEL_REVISION


class Encoder:
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.state = "not_loaded"
        self.device = None
        self.error = None
        self.load_seconds = None

    def _load(self):
        if self.model is not None:
            return
        self.state = "loading"
        self.error = None
        started = time.perf_counter()
        try:
            import torch
            from sentence_transformers import SentenceTransformer

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = (
                torch.bfloat16
                if self.device == "cuda" and torch.cuda.is_bf16_supported()
                else torch.float32
            )
            self.model = SentenceTransformer(
                MODEL_ID,
                revision=MODEL_REVISION,
                device=self.device,
                config_kwargs={"audio_config": None},
                model_kwargs={"torch_dtype": dtype},
            )
            self.state = "ready"
            self.load_seconds = round(time.perf_counter() - started, 2)
        except Exception:
            self.state = "error"
            self.error = "Model could not load. Check network access, free RAM and the server log."
            raise

    def encode(self, content, prompt_name=None):
        with self.lock:
            self._load()
            kwargs = {"normalize_embeddings": True, "show_progress_bar": False, "batch_size": 1}
            if prompt_name:
                kwargs["prompt_name"] = prompt_name
            vector = np.asarray(self.model.encode(content, **kwargs), dtype=np.float32).reshape(-1)
            if vector.shape != (768,) or not np.isfinite(vector).all():
                raise ValueError("Model produced an invalid embedding; no index was published.")
            return vector / max(float(np.linalg.norm(vector)), 1e-12)

    def status(self):
        return {
            "state": self.state,
            "device": self.device,
            "error": self.error,
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "load_seconds": self.load_seconds,
        }


encoder = Encoder()
