import io

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from elevenlabs.client import ElevenLabs

import config

client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)


def _wav_bytes_to_numpy(wav_bytes: bytes) -> tuple[np.ndarray, int]:
    """
    Decode WAV bytes returned by the TTS API into a NumPy array that
    sounddevice can play. Returns (audio_array, sample_rate).
    """
    buffer = io.BytesIO(wav_bytes)
    sample_rate, audio = wav.read(buffer)
    # Normalize to float32 in range [-1.0, 1.0] for sounddevice
    audio = audio.astype(np.float32) / config.INT16_MAX
    return audio, sample_rate


def speak(text: str) -> None:
    """
    Convert text to speech using the ElevenLabs TTS API and play it through
    the system speakers. Blocks until playback is complete so responses
    do not overlap with the next recording cycle.
    Called by main.py after llm.py returns a reply.
    """
    chunks = client.text_to_speech.convert(
        voice_id = config.TTS_VOICE_ID,
        text = text,
        model_id = config.TTS_MODEL,
        output_format = "wav_24000",   # raw WAV so scipy can decode it directly
    )
    wav_bytes = b"".join(chunks)

    audio, sample_rate = _wav_bytes_to_numpy(wav_bytes)

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