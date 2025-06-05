# Music Matcher System Design Document

### Architecture Overview

System Layers: A fully developed version of the Music Matcher app system is one composed of distinct layers for audio ingestion, fingerprinting, storage, and querying via an API. By separating out each of these concerns, we can then scale and maintain each part independently for better performance and reliability. Furhtermore, this design better supports distribyted teamwork efforts. An ingestion pipeline will handles new audio files, generating fingerprints and storing them. A matching engine takes an input clip and finds a matching song from the fingerprint database. The API layer (FastAPI) provides endpoints for uploading tracks to fingerprint and for querying matches. Although this is already implemented, this can be better modularised. Furthermore, we will also introduce background processing and queues to handle heavy audio computations without blocking user requests; improving responsiveness and throughput.

#### 1. Ingestion & Fingerprinting Pipeline

#### 2. Audio Matching Workflow

#### 3. Scalable Storage & Fault Tolerance
* Fingerprint Store:
* Object Storage:
* API Layer:
* Asynchronous Processing: 
