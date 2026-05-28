import io
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from openai import OpenAI

import config

client = OpenAI(api_key=config.OPENAI_API_KEY)


def _mp3_bytes_to_numpy(mp3_bytes: bytes) -> tuple[np.ndarray, int]:
    """
    Decode MP3 bytes returned by the TTS API into a NumPy array that
    sounddevice can play. Uses scipy to decode via an in-memory buffer.
    Returns (audio_array, sample_rate).
    """
    buffer = io.BytesIO(mp3_bytes)
    sample_rate, audio = wav.read(buffer)
    # Normalize to float32 in range [-1.0, 1.0] for sounddevice
    audio = audio.astype(np.float32) / config.INT16_MAX
    return audio, sample_rate


def speak(text: str) -> None:
    """
    Convert text to speech using the OpenAI TTS API and play it through
    the system speakers. Blocks until playback is complete so responses
    do not overlap with the next recording cycle.
    Called by main.py after llm.py returns a reply.
    """
    response = client.audio.speech.create(
        model=config.TTS_MODEL,
        voice=config.TTS_VOICE,
        input=text,
        response_format="wav",  # Request WAV directly so scipy can decode it
    )

    wav_bytes = response.content
    audio, sample_rate = _mp3_bytes_to_numpy(wav_bytes)

    sd.play(audio, samplerate=sample_rate)
    sd.wait()  # Block until playback finishes


def speak_cue(cue: str) -> None:
    """
    Play a short spoken activation or deactivation cue.
    Wraps speak() but is kept separate so activation.py can call it
    without importing the full TTS pipeline directly.
    Examples: "Activating.", "Going to sleep."
    """
    speak(cue)