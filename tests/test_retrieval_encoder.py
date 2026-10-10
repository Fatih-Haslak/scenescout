import numpy as np
import pytest
import sys
from types import SimpleNamespace

from scenescout import store
from scenescout.encoder import Encoder
from scenescout.retrieval import Retrieval, rank


def test_temporal_diversity_and_score_order(vector):
    rows = [
        {
            "id": str(i),
            "video_id": "a",
            "timestamp": i * 3,
            "interval": 3,
            "name": "a.mp4",
            "duration": 30,
        }
        for i in range(4)
    ]
    matrix = np.zeros((4, 768), dtype=np.float32)
    matrix[:, 0] = [0.9, 1, 0.8, 0.7]
    hits = rank(rows, matrix, vector, 2)
    assert [hit["timestamp"] for hit in hits] == [3, 9]
    assert [hit["score"] for hit in hits] == [1, 0.7]
    assert len(rank(rows, matrix, vector, 2, min_score=0.8)) == 1
    assert rank(rows, matrix * 0.4, vector, min_score=0.7) == []
    # Apply the raw score threshold before rounding the displayed score.
    assert rank(rows, matrix * 0.69999, vector, min_score=0.7) == []


def test_cached_vectors_refresh_after_publish_and_removal(add_video, vector):
    cache = Retrieval()
    add_video("a", "indexing")
    store.checkpoint("a", [("a-00000", "a", 0, vector.tobytes())])
    assert cache.snapshot()[0] == []
    store.update("a", status="ready")
    rows, matrix = cache.snapshot()
    assert len(rows) == 1
    assert cache.snapshot()[1] is matrix
    store.remove("a")
    assert cache.snapshot()[0] == []


@pytest.mark.parametrize(
    "bad",
    [np.zeros((1, 768)), np.ones((1, 767)), np.full((1, 768), np.nan), np.full((1, 768), np.inf)],
)
def test_invalid_model_vectors_rejected(bad):
    class Model:
        def encode(self, contents, **kwargs):
            return bad

    encoder = Encoder()
    encoder.model = Model()
    with pytest.raises(ValueError):
        encoder.encode("tree")


def test_batch_vectors_are_normalized():
    class Model:
        def encode(self, contents, **kwargs):
            assert kwargs["batch_size"] == 2
            assert kwargs["prompt_name"] == "SearchQuery"
            return np.ones((2, 768))

    encoder = Encoder()
    encoder.model = Model()
    assert np.allclose(
        np.linalg.norm(encoder.encode_many(["tree", "rabbit"], "SearchQuery"), axis=1), 1
    )


@pytest.mark.parametrize(
    "requested,available,bf16,device,dtype",
    [
        ("auto", False, False, "cpu", "fp32"),
        ("cpu", True, True, "cpu", "fp32"),
        ("auto", True, True, "cuda", "bf16"),
        ("cuda", True, False, "cuda", "fp32"),
    ],
)
def test_device_selection_uses_safe_dtype(monkeypatch, requested, available, bf16, device, dtype):
    monkeypatch.setenv("SCENESCOUT_DEVICE", requested)
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            cuda=SimpleNamespace(is_available=lambda: available, is_bf16_supported=lambda: bf16),
            bfloat16="bf16",
            float32="fp32",
        ),
    )
    calls = []
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(
            SentenceTransformer=lambda *args, **kwargs: calls.append(kwargs) or object()
        ),
    )
    encoder = Encoder()
    encoder._load()
    assert encoder.state == "ready"
    assert calls[0]["device"] == device
    assert calls[0]["model_kwargs"]["torch_dtype"] == dtype
    assert calls[0]["config_kwargs"]["audio_config"] is None


def test_forced_cuda_fails_clearly_when_unavailable(monkeypatch):
    monkeypatch.setenv("SCENESCOUT_DEVICE", "cuda")
    monkeypatch.setitem(
        sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    )
    monkeypatch.setitem(
        sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=object)
    )
    encoder = Encoder()
    with pytest.raises(ValueError, match="CUDA was requested"):
        encoder._load()
    assert encoder.state == "error"
