# music_matcher
Test app to match music.

This was inspired by [https://willdrevo.com/fingerprinting-and-audio-recognition-with-python/]this blog post. This is a lightweight custom implementation of Dejavu.

Audio loading:
- To support ingesting both MP3 and WAV files, I am using librosa.load(), which decodes using audioread and ffmpeg. I normalise the waveform and store fingerprints.

Testing:
- For positive testing, all 10 tracks are loaded, pre-generated query clips are then randomly selected and checked against the database. Tests pass if the query matches against the known matching track and fails if it mis-matches.
- For negative testing, a track not within the database has been sampled and this is posed as a query. Test passes when this fails to match.
- For testing file type, a non .wav .mp3 file is attempted to be ingested. Test passes when this fails.
