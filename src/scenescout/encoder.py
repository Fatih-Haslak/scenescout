"""Lazy, serialized model loading and inference. No fake fallback embeddings."""

import threading
import time
import os

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

            requested = os.getenv("SCENESCOUT_DEVICE", "auto")
            if requested not in {"auto", "cpu", "cuda"}:
                raise ValueError("SCENESCOUT_DEVICE must be auto, cpu or cuda")
            if requested == "cuda" and not torch.cuda.is_available():
                raise ValueError("CUDA was requested but this PyTorch installation cannot use it")
            self.device = "cuda" if requested != "cpu" and torch.cuda.is_available() else "cpu"
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
        return self.encode_many([content], prompt_name)[0]

    def encode_many(self, contents, prompt_name=None):
        if not contents:
            return np.empty((0, 768), dtype=np.float32)
        with self.lock:
            self._load()
            kwargs = {
                "normalize_embeddings": True,
                "show_progress_bar": False,
                "batch_size": len(contents),
            }
            if prompt_name:
                kwargs["prompt_name"] = prompt_name
            vectors = np.asarray(self.model.encode(contents, **kwargs), dtype=np.float32)
            if vectors.shape != (len(contents), 768) or not np.isfinite(vectors).all():
                raise ValueError("Model produced an invalid embedding; no index was published.")
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms <= 1e-12):
                raise ValueError("Model produced a zero embedding; no index was published.")
            return vectors / norms

    def batch_size(self):
        value = int(os.getenv("SCENESCOUT_BATCH_SIZE", "2"))
        if not 1 <= value <= 16:
            raise ValueError("SCENESCOUT_BATCH_SIZE must be between 1 and 16")
        return value

    def status(self):
        return {
            "state": self.state,
            "device": self.device,
            "error": self.error,
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "load_seconds": self.load_seconds,
            "batch_size": self.batch_size(),
        }


encoder = Encoder()
