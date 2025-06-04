import sys
import os
import random
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TRACKS_DIR = "data/tracks"
QUERIES_DIR = "data/queries"

@pytest.fixture(scope="session", autouse=True)
def ingest_all_tracks():
    for filename in os.listdir(TRACKS_DIR):
        if filename.endswith(".mp3") or filename.endswith(".wav"):
            with open(os.path.join(TRACKS_DIR, filename), "rb") as f:
                response = client.post("/ingest", files={"file": (filename, f, "audio/mpeg")})
                assert response.status_code == 200
                assert response.json()["status"] == "ingested"

def get_random_queries(n=3):
    query_files = [
        f for f in os.listdir(QUERIES_DIR)
        if f.endswith(".mp3") and f.lower() != "notfound.mp3"
    ]
    return random.sample(query_files, min(n, len(query_files)))

def test_match_random_queries_with_scores():
    queries = get_random_queries()
    for query_file in queries:
        with open(os.path.join(QUERIES_DIR, query_file), "rb") as f:
            response = client.post("/match", files={"file": (query_file, f, "audio/mpeg")})

        if response.status_code != 200:
            print(f"❌ Match failed for: {query_file} → Status: {response.status_code}")
        assert response.status_code == 200

        result = response.json()
        print(f"Matched: {result['filename']} | Score: {result['confidence_score']}")
        expected_track = query_file.split("_clip")[0] + ".mp3"
        matched_track = result["filename"]
        score = result["confidence_score"]
        is_correct = matched_track.lower() == expected_track.lower()

        print(f"Query: {query_file} → Matched: {matched_track} | Score: {score} | ✅ Correct: {is_correct}")
        assert is_correct

def test_ingest_reject_non_audio():
    response = client.post("/ingest", files={"file": ("bad.txt", b"this is not audio", "text/plain")})
    assert response.status_code == 400

def test_match_no_match_found():
    with open(os.path.join(QUERIES_DIR, "notfound.mp3"), "rb") as f:
        response = client.post("/match", files={"file": ("notfound.mp3", f, "audio/mpeg")})
    assert response.status_code in [404, 500]
