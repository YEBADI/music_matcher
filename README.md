# music_matcher
Test app to match music.

This was inspired by [https://willdrevo.com/fingerprinting-and-audio-recognition-with-python/]this blog post. This is a lightweight custom implementation of Dejavu.

Audio loading:
- To support ingesting both MP3 and WAV files, I am using librosa.load(), which decodes using audioread and ffmpeg. I normalise the waveform and store fingerprints.
