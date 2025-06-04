from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from scipy.signal import correlate
from pathlib import Path
import librosa
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI()

# fingerprint memory store
fingerprint_db = []
track_counter = 1


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    global track_counter

    if not (file.filename.endswith(".mp3") or file.filename.endswith(".wav")):
        raise HTTPException(
            status_code=400, detail="Only .mp3 or .wav files are supported."
        )

    try:
        contents = await file.read()
        # Use librosa with audioread backend (FFmpeg) to load MP3
        import io

        audio, sr = librosa.load(io.BytesIO(contents), sr=11025, mono=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {e}")

    # Normalise the waveform
    audio = audio - np.mean(audio)
    norm = np.linalg.norm(audio)
    if norm > 0:
        audio = audio / norm

    # Store
    fingerprint_db.append(
        {
            "id": track_counter,
            "filename": file.filename,
            "fingerprint": audio,
            "sr": sr,
        }
    )

    track_id = track_counter
    track_counter += 1

    return {
        "status": "ingested",
        "track_id": track_id,
        "filename": file.filename,
        "sample_rate": sr,
        "duration_sec": round(len(audio) / sr, 2),
    }


@app.post("/match")
async def match(file: UploadFile = File(...)):
    if not (file.filename.endswith(".mp3") or file.filename.endswith(".wav")):
        raise HTTPException(
            status_code=400, detail="Only .mp3 or .wav files are supported."
        )

    try:
        contents = await file.read()
        import io

        query_audio, sr = librosa.load(io.BytesIO(contents), sr=11025, mono=True)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process query audio: {e}"
        )

    query_audio = query_audio - np.mean(query_audio)
    norm = np.linalg.norm(query_audio)
    if norm > 0:
        query_audio = query_audio / norm

    best_match = None
    highest_score = -1
    best_offset = 0

    for track in fingerprint_db:
        stored_audio = track["fingerprint"]

        # Correlate full audio with the short query
        correlation = correlate(stored_audio, query_audio, mode="valid")
        peak = np.max(correlation)
        offset = np.argmax(correlation) / track["sr"]  # seconds

        if peak > highest_score:
            best_match = track
            highest_score = peak
            best_offset = offset

    if not best_match or highest_score is None or highest_score < 0.05:
        raise HTTPException(status_code=404, detail="No match found")

    return {
        "match_track_id": best_match["id"],
        "filename": best_match["filename"],
        "timestamp_offset_sec": round(best_offset, 2),
        "confidence_score": round(float(highest_score), 4),
    }
