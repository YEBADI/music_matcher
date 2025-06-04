from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
from typing import List
from scipy.signal import correlate
from pathlib import Path
import librosa
import numpy as np
import io

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI()

# fingerprint memory store
fingerprint_db = []
track_counter = 1


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/clear", response_class=HTMLResponse)
async def clear_cache(request: Request):
    global fingerprint_db, track_counter
    fingerprint_db.clear()
    track_counter = 1
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "status": "cleared",
            "ingested_tracks": [],
            "match_result": None,
        },
    )


@app.post("/ingest")
async def ingest(request: Request, files: List[UploadFile] = File(...)):
    global track_counter

    newly_ingested = []

    for file in files:
        if not (file.filename.endswith(".mp3") or file.filename.endswith(".wav")):
            continue  # Skip non-audio files silently

        try:
            contents = await file.read()
            import io

            audio, sr = librosa.load(io.BytesIO(contents), sr=11025, mono=True)
        except Exception:
            continue  # Skip file on error, but continue with others

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

        newly_ingested.append(
            {
                "track_id": track_counter,
                "filename": file.filename,
                "duration_sec": round(len(audio) / sr, 2),
            }
        )

        track_counter += 1

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "ingested": newly_ingested,  # tracks just added in this session
            "ingested_tracks": [
                f"{t['id']}: {t['filename']}" for t in fingerprint_db
            ],  # all so far
            "match_result": None,
        },
    )


@app.post("/match")
async def match(request: Request, file: UploadFile = File(...)):
    if not (file.filename.endswith(".mp3") or file.filename.endswith(".wav")):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Invalid file type. Please upload an MP3 or WAV.",
                "ingested_tracks": [
                    f"{t['id']}: {t['filename']}" for t in fingerprint_db
                ],
                "match_result": None,
            },
            status_code=400,
        )

    try:
        contents = await file.read()
        import io

        query_audio, sr = librosa.load(io.BytesIO(contents), sr=11025, mono=True)
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": f"Failed to process query audio: {e}",
                "ingested_tracks": [
                    f"{t['id']}: {t['filename']}" for t in fingerprint_db
                ],
                "match_result": None,
            },
            status_code=500,
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
        from scipy.signal import correlate

        correlation = correlate(stored_audio, query_audio, mode="valid")
        peak = np.max(correlation)
        offset = np.argmax(correlation) / track["sr"]

        if peak > highest_score:
            best_match = track
            highest_score = peak
            best_offset = offset

    if not best_match or highest_score < 0.05:
        match_result = {"message": "No match found."}
    else:
        match_result = {
            "filename": best_match["filename"],
            "confidence_score": round(float(highest_score), 4),
            "offset": round(best_offset, 2),
        }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "match_result": match_result,
            "ingested_tracks": [f"{t['id']}: {t['filename']}" for t in fingerprint_db],
        },
    )
