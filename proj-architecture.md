# SPOT AI - Proof of Concept Architecture

## Overview

This document describes the architecture of the SPOT AI proof of concept. The PoC implements a voice-based conversational AI pipeline using a laptop, USB microphone, and speakers. It serves as the foundation before integrating with the Boston Dynamics SPOT robot.

The system operates in two states — **idle** and **active** — and can be switched between them via a voice command or a manual keyboard input.

-----

## Project Structure

```
spot-ai/
├── main.py            # Entry point — runs the state machine and main loop
├── stt.py             # Speech-to-text module (mic input + Whisper transcription)
├── llm.py             # LLM module (GPT conversation + conversation memory)
├── tts.py             # Text-to-speech module (OpenAI TTS + audio playback)
├── activation.py      # Activation/deactivation logic (voice and manual)
├── config.py          # Configuration (API keys, model settings, constants)
└── requirements.txt   # Python dependencies
```

-----

## System States

The system has two states that control whether it responds to conversation input.

```
┌───────────────────────────────────────────────────────────┐
│                                                           │
│   [IDLE]  ──── voice phrase OR key press ────>  [ACTIVE]  │
│                                                           │
│   [ACTIVE] ──── voice phrase OR key press ───>  [IDLE]    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

|State   |Behavior                                                             |
|--------|---------------------------------------------------------------------|
|`IDLE`  |Mic is open but only listening for the activation phrase or key press|
|`ACTIVE`|Full pipeline runs — listens, transcribes, generates reply, speaks   |

-----

## Activation & Deactivation

Both voice and manual methods are supported and can be used interchangeably at any time.

### Voice Activation

- System is always listening at low level in idle state
- User speaks the **activation phrase** (e.g., `"Hey SPOT"`)
- `activation.py` detects the phrase in the transcribed audio
- System transitions to `ACTIVE` state and plays a confirmation sound

### Voice Deactivation

- While in `ACTIVE` state, user speaks the **deactivation phrase** (e.g., `"Goodbye SPOT"`)
- `activation.py` checks each transcription for the phrase before passing to the LLM
- System transitions to `IDLE` state and plays a shutdown sound

### Manual Activation / Deactivation

- Pressing the **Enter key** toggles between `IDLE` and `ACTIVE` at any time
- A status line in the console always shows the current state
- Useful for testing, demos, or when voice detection is unreliable

-----

## Data Flow

### Idle State

```
[USB Microphone]
      |
      | raw audio (short clip)
      v
[stt.py]  ──────────────────>  OpenAI Whisper API
      |
      | transcribed text
      v
[activation.py]
      |
      | activation phrase detected?
      |
      ├── NO  ──>  discard, loop back to listening
      |
      └── YES ──>  switch to ACTIVE state
```

### Active State

```
[USB Microphone]
      |
      | raw audio (PCM)
      v
[stt.py]  ──────────────────>  OpenAI Whisper API
      |
      | transcribed text (string)
      v
[activation.py]  ── deactivation phrase? ──> switch to IDLE state
      |
      | (no deactivation phrase — pass to LLM)
      v
[llm.py]  ──────────────────>  OpenAI GPT-4o API
      |                         (with conversation history)
      | reply text (string)
      v
[tts.py]  ──────────────────>  OpenAI TTS API
      |
      | synthesized audio
      v
[Speakers]
```

-----

## Module Descriptions

### `config.py`

Holds all configuration values in one place so no settings are hardcoded across modules.

**Responsibilities:**

- Store the OpenAI API key
- Define model names (Whisper model, GPT model, TTS voice)
- Set audio constants (sample rate, silence threshold, max recording duration)
- Set the system prompt that defines SPOT’s personality
- Define the activation and deactivation phrases
- Define the manual toggle key

-----

### `activation.py` — Activation & Deactivation

Manages the system state and all logic for switching between idle and active.

**Responsibilities:**

- Hold the current system state (`IDLE` or `ACTIVE`)
- Check transcribed text for the activation phrase
- Check transcribed text for the deactivation phrase
- Listen for the manual key press on a background thread
- Expose a simple `is_active()` method for `main.py` to check state
- Play an audio cue when state changes (e.g., a beep or short TTS phrase)

**Key behavior:**

- Phrase detection is case-insensitive and checks if the phrase appears anywhere in the transcription
- Manual key toggle runs on a separate thread so it does not block the audio pipeline
- On activation, conversation history in `llm.py` is optionally reset

-----

### `stt.py` — Speech-to-Text

Handles all audio input and transcription.

**Responsibilities:**

- Access the USB microphone via `sounddevice`
- Record audio until silence is detected (voice activity detection)
- Send the recorded audio to the OpenAI Whisper API
- Return the transcribed text as a string

**Key behavior:**

- Runs in both idle and active states (idle uses shorter clip length)
- Uses a silence threshold to determine when the user has stopped speaking
- Buffers audio in `numpy` arrays before sending to Whisper

-----

### `llm.py` — Language Model

Manages conversation logic and memory.

**Responsibilities:**

- Maintain a running list of messages (conversation history)
- Prepend the system prompt on every API call
- Send user input + full history to GPT-4o
- Append the assistant’s reply to history
- Return the reply text as a string
- Expose a `reset()` method to clear history on deactivation

**Key behavior:**

- Conversation history persists while the system stays in `ACTIVE` state
- History can be cleared when the system deactivates (configurable in `config.py`)
- The system prompt sets SPOT’s personality and communication style

-----

### `tts.py` — Text-to-Speech

Converts the LLM reply into spoken audio and plays it.

**Responsibilities:**

- Send reply text to the OpenAI TTS API
- Receive the audio response (MP3 bytes)
- Play the audio through the system speakers using `sounddevice` or `scipy`
- Play short activation and deactivation audio cues

**Key behavior:**

- Blocks the main loop while audio is playing so responses do not overlap
- Voice model and speaking style are set in `config.py`

-----

### `main.py` — Main Loop

The entry point that ties all modules together and runs the state machine.

**Responsibilities:**

- Initialize all modules
- Start the manual key listener thread from `activation.py`
- Run the outer loop that checks system state each iteration
- Route audio to the correct handler based on current state
- Handle keyboard interrupt (Ctrl+C) for clean shutdown
- Log state and each conversation turn to the console

**Loop logic:**

```
1. Check activation.is_active()

   If IDLE:
     a. stt.listen_short()       → short audio clip
     b. activation.check(text)   → if phrase detected, switch to ACTIVE

   If ACTIVE:
     a. stt.listen()             → full audio clip
     b. activation.check(text)   → if deactivation phrase, switch to IDLE
     c. llm.chat(text)           → get assistant reply
     d. tts.speak(reply)         → play audio response

2. Repeat
```

-----

## Technology Stack

|Layer               |Technology                           |Purpose                                 |
|--------------------|-------------------------------------|----------------------------------------|
|Audio Input         |`sounddevice`, `numpy`               |Record from USB microphone              |
|Speech-to-Text      |OpenAI Whisper API                   |Transcribe spoken audio to text         |
|Activation Detection|`activation.py`                      |Phrase matching + manual key toggle     |
|Language Model      |OpenAI GPT-4o                        |Generate conversational responses       |
|Text-to-Speech      |OpenAI TTS API                       |Convert reply text to spoken audio      |
|Audio Output        |`scipy`, `sounddevice`               |Play synthesized speech through speakers|
|Manual Toggle       |`keyboard` or `threading` + `input()`|Listen for key press in background      |
|Configuration       |`config.py`                          |Centralize all settings and API keys    |

-----

## Dependencies

```
openai       # Whisper, GPT-4o, and TTS API client
sounddevice  # Microphone input and audio playback
numpy        # Audio buffer handling
scipy        # WAV file writing for Whisper input
keyboard     # Manual key press detection (cross-platform)
```

Install with:

```bash
pip install openai sounddevice numpy scipy keyboard
```

-----

## Environment Setup

The OpenAI API key must be set as an environment variable before running:

```bash
export OPENAI_API_KEY="your-key-here"
```

Run the program:

```bash
python main.py
```

Console output will show current state at all times:

```
[IDLE]   Listening for activation phrase or press Enter...
[ACTIVE] Listening...
[ACTIVE] User: "What is the weather like?"
[ACTIVE] SPOT: "I don't have access to live weather data, but..."
```

-----

## PoC Limitations

- Phrase detection relies on Whisper transcription accuracy — noisy environments may cause missed detections
- Conversation history grows unbounded during an active session (no summarization or trimming)
- No integration with the SPOT SDK or robot hardware
- No error recovery if an API call fails mid-conversation

-----

## Future Integration (Post-PoC)

Once the PoC is validated, the following additions will be needed for SPOT:

- Replace laptop mic/speakers with a hardware audio payload on SPOT
- Replace phrase detection with a dedicated wake word engine (e.g., `pvporcupine`) for lower latency and offline activation
- Replace manual key toggle with a physical button on the robot body
- Integrate Boston Dynamics SPOT SDK (`bosdyn-client`) to trigger robot behaviors based on conversation context
- Move compute to an onboard payload (e.g., NVIDIA Jetson) or tether to a companion laptop via the SPOT API