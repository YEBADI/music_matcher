import os
import io
import time
import argparse
import librosa
import numpy as np
import psutil
from scipy.signal import correlate
from app.main import fingerprint_db, track_counter

# Global
track_counter = 1


def normalize_audio(audio):
    audio = audio - np.mean(audio)
    norm = np.linalg.norm(audio)
    return audio / norm if norm > 0 else audio


def get_memory_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024**2  # in MB


def ingest_tracks(tracks_dir):
    global track_counter
    start_mem = get_memory_usage_mb()

    for filename in os.listdir(tracks_dir):
        if not (filename.endswith(".mp3") or filename.endswith(".wav")):
            continue
        filepath = os.path.join(tracks_dir, filename)
        audio, sr = librosa.load(filepath, sr=11025, mono=True)
        audio = normalize_audio(audio)
        fingerprint_db.append(
            {
                "id": track_counter,
                "filename": filename,
                "fingerprint": audio,
                "sr": sr,
            }
        )
        track_counter += 1

    end_mem = get_memory_usage_mb()
    print(f"✅ Ingested {len(fingerprint_db)} tracks.")
    print(
        f"🧠 Memory usage: {round(start_mem, 2)}MB → {round(end_mem, 2)}MB ({round(end_mem - start_mem, 2)}MB increase)"
    )


def match_query(query_audio, sr):
    query_audio = normalize_audio(query_audio)

    results = []
    for track in fingerprint_db:
        stored = track["fingerprint"]
        corr = correlate(stored, query_audio, mode="valid")
        peak = np.max(corr)
        offset = np.argmax(corr) / track["sr"]
        results.append(
            {
                "filename": track["filename"],
                "score": peak,
                "offset": round(offset, 2),
            }
        )

    return sorted(results, key=lambda x: x["score"], reverse=True)


def evaluate_queries(queries_dir, cutoff=0.05):
    correct = 0
    total = 0
    latencies = []

    for filename in os.listdir(queries_dir):
        if not (filename.endswith(".mp3") or filename.endswith(".wav")):
            continue

        filepath = os.path.join(queries_dir, filename)
        query_audio, sr = librosa.load(filepath, sr=11025, mono=True)

        start_time = time.perf_counter()
        matches = match_query(query_audio, sr)
        elapsed = time.perf_counter() - start_time
        latencies.append(elapsed)

        if not matches or matches[0]["score"] < cutoff:
            print(f"❌ {filename}: No match above cutoff ({cutoff}) [⏱ {elapsed:.3f}s]")
            continue

        best = matches[0]
        expected = filename.split("_clip")[0] + ".mp3"
        match_correct = best["filename"].lower() == expected.lower()
        print(
            f"{'✅' if match_correct else '❌'} {filename} → {best['filename']} | Score: {round(best['score'], 4)} [⏱ {elapsed:.3f}s]"
        )

        correct += int(match_correct)
        total += 1

    avg_latency = np.mean(latencies) if latencies else 0
    print(f"\n🎯 Accuracy: {correct}/{total} = {round(100 * correct / total, 2)}%")
    print(f"⏱ Average Query Latency: {avg_latency:.3f} seconds")
    print(f"📦 Total Tracks in DB: {len(fingerprint_db)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate audio matcher accuracy and performance."
    )
    parser.add_argument(
        "--tracks", default="data/tracks", help="Folder with reference tracks"
    )
    parser.add_argument(
        "--queries", default="data/queries", help="Folder with audio clips"
    )
    parser.add_argument("--cutoff", type=float, default=0.05, help="Match score cutoff")
    args = parser.parse_args()

    ingest_tracks(args.tracks)
    evaluate_queries(args.queries, cutoff=args.cutoff)
