import pytest

from scenescout import api, indexer, store, imports
from scenescout.retrieval import retrieval


@pytest.fixture
def library(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(api, "DATA_DIR", tmp_path)
    monkeypatch.setattr(indexer, "DATA_DIR", tmp_path)
    monkeypatch.setattr(imports, "DATA_DIR", tmp_path)
    store.initialize()
    retrieval.cached_generation = -1
    return tmp_path


@pytest.fixture
def add_video(library):
    def add(video_id="a", status="ready", interval=3):
        with store.connection() as db:
            db.execute(
                """INSERT INTO videos(id,name,extension,digest,size,interval,status,duration)
                VALUES(?,?,?,?,?,?,?,?)""",
                (video_id, f"{video_id}.mp4", ".mp4", video_id, 1, interval, status, 30),
            )
        store.invalidate()
        return video_id

    return add


@pytest.fixture
def vector():
    import numpy as np

    result = np.zeros(768, dtype=np.float32)
    result[0] = 1
    return result
