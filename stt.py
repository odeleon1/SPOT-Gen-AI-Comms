import io

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
from elevenlabs.client import ElevenLabs

import config

client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)


def _record_until_silence(max_seconds: float) -> np.ndarray:
    """
    Record audio from the microphone until silence is detected or max_seconds
    is reached. Returns the recorded audio as a NumPy array (float32, mono).

    Silence detection uses RMS amplitude. Recording stops when SILENCE_DURATION
    consecutive seconds fall below SILENCE_THRESHOLD, as defined in config.py.
    """
    frames_per_check = int(config.SAMPLE_RATE * 0.1)   # evaluate silence every 100ms
    max_frames       = int(config.SAMPLE_RATE * max_seconds)
    silence_frames   = int(config.SAMPLE_RATE * config.SILENCE_DURATION)

    recorded   = []
    silent_for = 0          # running count of consecutive silent frames

    with sd.InputStream(
        samplerate = config.SAMPLE_RATE,
        channels = 1,
        dtype = "float32",
        blocksize = frames_per_check,
    ) as stream:
        while True:
            chunk, _ = stream.read(frames_per_check)
            chunk = chunk.flatten()
            recorded.append(chunk)

            # RMS amplitude check
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            if rms < config.SILENCE_THRESHOLD:
                silent_for += len(chunk)
            else:
                silent_for = 0  # reset on any speech-level audio

            total_frames = sum(len(c) for c in recorded)

            if silent_for >= silence_frames:
                break
            if total_frames >= max_frames:
                break

    return np.concatenate(recorded, axis=0)


def _numpy_to_wav_bytes(audio: np.ndarray) -> bytes:
    """
    Encode a float32 NumPy array as WAV bytes (in-memory, no temp file).
    Converts to int16 PCM before encoding, which Scribe expects.
    """
    pcm = (audio * config.INT16_MAX).astype(np.int16)
    buffer = io.BytesIO()
    wav.write(buffer, config.SAMPLE_RATE, pcm)
    buffer.seek(0)
    return buffer.read()


def _transcribe(audio: np.ndarray) -> str:
    """
    Send a NumPy audio array to the ElevenLabs Scribe API and return the
    transcribed text as a lowercase string.
    """
    wav_bytes = _numpy_to_wav_bytes(audio)
    audio_file = io.BytesIO(wav_bytes)
    audio_file.name = "audio.wav"   # Scribe requires a filename with extension

    response = client.speech_to_text.convert(
        model_id = config.STT_MODEL,
        file = audio_file,
    )
    return response.text.strip().lower()


def listen_short() -> str:
    """
    Record a short audio clip (idle state) and return the transcription.
    Uses MAX_RECORD_SECONDS / 3 as the cap to keep idle polling lightweight.
    Called by main.py when the system is IDLE to check for the activation phrase.
    """
    max_seconds = config.MAX_RECORD_SECONDS / 3
    audio = _record_until_silence(max_seconds)
    return _transcribe(audio)


def listen() -> str:
    """
    Record a full-length audio clip (active state) and return the transcription.
    Uses MAX_RECORD_SECONDS as the cap.
    Called by main.py when the system is ACTIVE to capture user input.
    """
    audio = _record_until_silence(config.MAX_RECORD_SECONDS)
    return _transcribe(audio)