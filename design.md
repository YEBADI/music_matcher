# Music Matcher System Design Document

### Architecture Overview

System Layers: A fully developed version of the Music Matcher app system is one composed of distinct layers for audio ingestion, fingerprinting, storage, and querying via an API. By separating out each of these concerns, we can then scale and maintain each part independently for better performance and reliability. Furhtermore, this design better supports distribyted teamwork efforts. An ingestion pipeline will handles new audio files, generating fingerprints and storing them. A matching engine takes an input clip and finds a matching song from the fingerprint database. The API layer (FastAPI) provides endpoints for uploading tracks to fingerprint and for querying matches. Although this is already implemented, this can be better modularised. Furthermore, we will also introduce background processing and queues to handle heavy audio computations without blocking user requests; improving responsiveness and throughput.

#### 1. Ingestion & Fingerprinting Pipeline

In the current implementation, the end user uploads the audio (MP3/WAV) via the FastAPI endpoint and it is immediately stored into memory, processed into a fingerprint via librosa and this fingerprint is stored. However, in a scaled up version of Music Matcher, we would decouple this process. Instead of processing immediately, the API can store the raw audio file in a dedicated S3 database and enqueue a fingerprinting task to a worker queue (e.g. via a Celery worker task, which would be appropriate here since this is already pythonic and Celery is coded in Python and can seamlessly integrate). The Celery background worker can pick up the task of retrieving the audio from the S3 database and then use librosa to compute the respective audio fingerprint.  By offloading this fingerprinting job to a worker process, the API responds immediately to the upload request with an acknowledgment, while the heavy lifting happens in the background (i.e. this decoupling ensures that the user isn’t stuck waiting on a long processing step). The fingerprint data (and the extracted metadata - such as the song title and length of the song) can then be stored in a dedicated fingerprint database. This fingerprint database can be a managed PostgreSQL (Amazon RDS) or Aurora instance, which efficiently indexes and queries fingerprint data (hence why this would be the prefered option over opting for a standard S3 service which does not provide processing) - i.e. storing fingerprints in a relational database or specialised search index allows fast lookup during matching. This async pipeline improves user experience and lets the system ingest songs in batch without overwhelming the web server.

#### 2. Audio Matching Workflow

#### 3. Scalable Storage & Fault Tolerance
* Fingerprint Store:
* Object Storage:
* API Layer:
* Asynchronous Processing: 

