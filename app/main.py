from fastapi import FastAPI, UploadFile, File, HTTPException
import librosa
import numpy as np

app = FastAPI()

# fingerprint memory store
fingerprint_db = []
track_counter = 1



@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    global track_counter

    if not (file.filename.endswith(".mp3") or file.filename.endswith(".wav")):
        raise HTTPException(status_code=400, detail="Only .mp3 or .wav files are supported.")

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
    fingerprint_db.append({
        "id": track_counter,
        "filename": file.filename,
        "fingerprint": audio,
        "sr": sr,
    })

    track_id = track_counter
    track_counter += 1

    return {
        "status": "ingested",
        "track_id": track_id,
        "filename": file.filename,
        "sample_rate": sr,
        "duration_sec": round(len(audio) / sr, 2),
    }
