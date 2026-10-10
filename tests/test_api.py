import io

import pytest
import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from scenescout import api, store


@pytest.fixture
def client(library, monkeypatch):
    monkeypatch.setattr(api.indexer, "submit", lambda video_id: True)
    with TestClient(api.app, base_url="http://127.0.0.1:8765") as client:
        yield client


@pytest.mark.parametrize(
    "filename,interval,content",
    [
        ("x.txt", 3, b"x"),
        ("x.mp4", 0, b"x"),
        ("x.mp4", "nan", b"x"),
        ("x.mp4", 31, b"x"),
        ("x.mp4", 3, b""),
    ],
)
def test_invalid_import_leaves_no_files(client, library, filename, interval, content):
    response = client.post(
        "/api/videos", files={"file": (filename, content)}, data={"interval": interval}
    )
    assert response.status_code == 400
    assert not list((library / "videos").iterdir())
    assert store.videos() == []


def test_duplicate_import_keeps_one_copy(client, library):
    first = client.post("/api/videos", files={"file": ("../../x.mp4", b"same")}).json()
    second = client.post("/api/videos", files={"file": ("another.mp4", b"same")}).json()
    assert second == {"id": first["id"], "duplicate": True}
    assert len(list((library / "videos").iterdir())) == 1
    assert store.video(first["id"])["name"] == "x.mp4"


def test_upload_limit_removes_partial_copy(client, library, monkeypatch):
    monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 2)
    assert client.post("/api/videos", files={"file": ("x.mp4", b"abc")}).status_code == 413
    assert not list((library / "videos").iterdir())


def test_local_boundary_and_security_headers(client):
    assert client.get("/api/status", headers={"host": "evil.example"}).status_code == 403
    assert (
        client.post(
            "/api/search", json={"query": "tree"}, headers={"origin": "https://evil.example"}
        ).status_code
        == 403
    )
    response = client.get("/")
    assert response.status_code == 200
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert client.get("/docs").status_code == 200


def test_search_validation_and_empty_library(client, monkeypatch):
    def forbidden(*args):
        raise AssertionError("empty library must not load the model")

    monkeypatch.setattr(api.encoder, "encode", forbidden)
    assert client.post("/api/search", json={"query": "tree"}).json()["results"] == []
    assert client.post("/api/search", json={"query": " "}).status_code == 400
    assert client.post("/api/search", json={"query": "tree", "limit": 31}).status_code == 422
    assert client.post("/api/search", json={"query": "tree", "video_id": "no"}).status_code == 404


def test_scoped_search_and_model_error(client, add_video, vector, monkeypatch):
    for video_id in ["a", "b"]:
        add_video(video_id)
        store.checkpoint(video_id, [(video_id + "-00000", video_id, 0, vector.tobytes())])
    monkeypatch.setattr(api.encoder, "encode", lambda *args: vector)
    response = client.post("/api/search", json={"query": "tree", "video_id": "b"})
    assert [hit["video_id"] for hit in response.json()["results"]] == ["b"]

    def fail(*args):
        raise RuntimeError("inference unavailable")

    monkeypatch.setattr(api.encoder, "encode", fail)
    assert client.post("/api/search", json={"query": "tree"}).status_code == 503


def test_video_deleted_during_inference_is_not_returned(client, add_video, vector, monkeypatch):
    add_video()
    store.checkpoint("a", [("a-00000", "a", 0, vector.tobytes())])

    def remove_during_query(*args):
        store.remove("a")
        return vector

    monkeypatch.setattr(api.encoder, "encode", remove_during_query)
    assert client.post("/api/search", json={"query": "tree"}).json()["results"] == []


def test_resume_only_accepts_failed_or_paused_jobs(client, add_video):
    add_video("a", "paused")
    add_video("b", "ready")
    assert client.post("/api/videos/a/resume").status_code == 202
    assert client.post("/api/videos/b/resume").status_code == 409
    assert client.post("/api/videos/missing/resume").status_code == 404


def test_invalid_reference_image_rejected(client):
    assert client.post("/api/search/image", files={"file": ("x.png", b"bad")}).status_code == 400
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buffer, format="PNG")
    response = client.post("/api/search/image", files={"file": ("x.png", buffer.getvalue())})
    assert response.json()["results"] == []


def test_similarity_threshold_applies_to_text_and_image(client, add_video, vector, monkeypatch):
    add_video()
    store.checkpoint("a", [("a-00000", "a", 0, vector.tobytes())])
    query_vector = vector.copy()
    query_vector[0], query_vector[1] = 0.5, np.sqrt(0.75)
    monkeypatch.setattr(api.encoder, "encode", lambda *args: query_vector)
    assert len(client.post("/api/search", json={"query": "tree"}).json()["results"]) == 1
    response = client.post("/api/search", json={"query": "tree", "min_score": 0.7}).json()
    assert response["results"] == [] and response["searched_frames"] == 1
    assert response["min_score"] == 0.7
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buffer, format="PNG")
    assert (
        client.post(
            "/api/search/image",
            files={"file": ("x.png", buffer.getvalue())},
            data={"min_score": 0.7},
        ).json()["results"]
        == []
    )
    for value in ["nan", "inf", -1.01, 1.01]:
        assert (
            client.post("/api/search", json={"query": "tree", "min_score": value}).status_code
            == 422
        )
        assert (
            client.post(
                "/api/search/image",
                files={"file": ("x.png", buffer.getvalue())},
                data={"min_score": value},
            ).status_code
            == 422
        )
