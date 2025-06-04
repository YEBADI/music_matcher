import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ingest_valid_file():
    with open("data/tracks/Mutant.mp3", "rb") as f:
        response = client.post("/ingest", files={"file": ("Mutant.mp3", f, "audio/mpeg")})
    assert response.status_code == 200
    assert response.json()["status"] == "ingested"

def test_match_valid_query():
    with open("data/queries/mutant_clip.mp3", "rb") as f:
        response = client.post("/match", files={"file": ("mutant_clip.mp3", f, "audio/mpeg")})
    assert response.status_code == 200
    result = response.json()
    assert "filename" in result
    assert "confidence_score" in result
    assert result["confidence_score"] > 0

def test_ingest_reject_non_audio():
    response = client.post("/ingest", files={"file": ("bad.txt", b"this is not audio", "text/plain")})
    assert response.status_code == 400

def test_match_no_match_found():
    with open("data/queries/notfound.mp3", "rb") as f:
    # A short clip from audio not in my database
        response = client.post("/match", files={"file": ("notfound.mp3", f, "audio/mpeg")})
    assert response.status_code in [404, 500]
