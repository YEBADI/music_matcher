from fastapi import FastAPI, UploadFile, File, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List
from pathlib import Path
from scipy.signal import correlate
import librosa
import numpy as np
import io

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI()

# fingerprint memory store
fingerprint_db = []
track_counter = 1
MATCH_THRESHOLD = 0.05  # configurable threshold


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
            continue

        try:
            contents = await file.read()
            audio, sr = librosa.load(io.BytesIO(contents), sr=11025, mono=True)
        except Exception:
            continue

        audio = audio - np.mean(audio)
        norm = np.linalg.norm(audio)
        if norm > 0:
            audio = audio / norm

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
            "ingested": newly_ingested,
            "ingested_tracks": [f"{t['id']}: {t['filename']}" for t in fingerprint_db],
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

    matches = []

    for track in fingerprint_db:
        stored_audio = track["fingerprint"]
        correlation = correlate(stored_audio, query_audio, mode="valid")
        peak = np.max(correlation)
        offset = np.argmax(correlation) / track["sr"]

        if peak >= MATCH_THRESHOLD:
            matches.append(
                {
                    "track_id": track["id"],
                    "filename": track["filename"],
                    "confidence_score": round(float(peak), 4),
                    "offset": round(offset, 2),
                }
            )

    match_result = (
        {"message": "No match found."}
        if not matches
        else {
            "matches": sorted(
                matches, key=lambda x: x["confidence_score"], reverse=True
            )
        }
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "match_result": match_result,
            "ingested_tracks": [f"{t['id']}: {t['filename']}" for t in fingerprint_db],
        },
    )
