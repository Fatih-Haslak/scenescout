"""Exact cosine retrieval with a bounded snapshot cache and temporal diversity."""

import threading

import numpy as np

from . import store


def rank(rows, matrix, vector, limit=12, min_score=-1):
    if not rows:
        return []
    scores = matrix @ vector
    picked = []
    for index in np.argsort(-scores, kind="stable"):
        if scores[index] < min_score:
            break
        row = rows[index]
        if any(
            hit["video_id"] == row["video_id"]
            and abs(hit["timestamp"] - row["timestamp"]) < row["interval"] * 2
            for hit in picked
        ):
            continue
        picked.append(
            {
                "id": row["id"],
                "video_id": row["video_id"],
                "name": row["name"],
                "timestamp": row["timestamp"],
                "duration": row["duration"],
                "score": round(float(scores[index]), 4),
                "thumbnail": f"/api/thumbnails/{row['id']}",
                "source_url": row.get("source_url"),
            }
        )
        if len(picked) == limit:
            break
    return picked


class Retrieval:
    def __init__(self):
        self.lock = threading.Lock()
        self.cached_generation = -1
        self.rows = []
        self.matrix = np.empty((0, 768), dtype=np.float32)

    def snapshot(self, video_id=None):
        with self.lock:
            current = store.generation()
            if current != self.cached_generation:
                with store.connection() as db:
                    rows = list(
                        db.execute(
                            """SELECT s.id,s.video_id,s.timestamp,s.vector,v.name,v.duration,v.interval,v.source_url
                        FROM scenes s JOIN videos v ON v.id=s.video_id
                        WHERE v.status='ready' ORDER BY s.video_id,s.timestamp"""
                        )
                    )
                self.matrix = (
                    np.stack([np.frombuffer(row["vector"], dtype="<f4") for row in rows])
                    if rows
                    else np.empty((0, 768), dtype=np.float32)
                )
                self.rows = [{k: row[k] for k in row.keys() if k != "vector"} for row in rows]
                self.cached_generation = current
            if video_id:
                indices = [i for i, row in enumerate(self.rows) if row["video_id"] == video_id]
                return [self.rows[i] for i in indices], self.matrix[indices]
            return self.rows, self.matrix


retrieval = Retrieval()
