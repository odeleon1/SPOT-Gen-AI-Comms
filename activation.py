import threading

import keyboard

import config
import llm
import tts

IDLE = "IDLE"
ACTIVE = "ACTIVE"

_state = IDLE
_lock = threading.Lock()


def is_active() -> bool:
    """Return True if the system is currently ACTIVE. Used by main.py each loop
    to decide which pipeline to run."""
    with _lock:
        return _state == ACTIVE


def _set_state(new_state: str) -> None:
    global _state
    with _lock:
        _state = new_state


def activate() -> None:
    """Switch to ACTIVE and play the activation cue. Does nothing if already active,
    so repeated triggers are safe."""
    if is_active():
        return
    _set_state(ACTIVE)
    print("[STATE] -> ACTIVE")
    tts.speak_cue("Activating.")


def deactivate() -> None:
    """Switch to IDLE and play the deactivation cue. Clears conversation history
    only if RESET_HISTORY_ON_DEACTIVATE is set in config.py."""
    if not is_active():
        return
    _set_state(IDLE)
    print("[STATE] -> IDLE")
    tts.speak_cue("Going to sleep.")
    if config.RESET_HISTORY_ON_DEACTIVATE:
        llm.reset()


def check(text: str) -> None:
    """Inspect a transcription and switch state if it contains the activation or
    deactivation phrase. Phrases are matched as substrings, and stt.py already
    lowercases its output so matching is case-insensitive."""
    if is_active():
        if config.DEACTIVATION_PHRASE in text:
            deactivate()
    else:
        if config.ACTIVATION_PHRASE in text:
            activate()


def _toggle() -> None:
    if is_active():
        deactivate()
    else:
        activate()


def _key_listener() -> None:
    # Blocks until the toggle key is pressed, flips the state, then waits again.
    # Runs forever on a daemon thread so it never blocks shutdown.
    while True:
        keyboard.wait(config.MANUAL_TOGGLE_KEY)
        _toggle()


def start_key_listener() -> None:
    """Start the manual toggle listener on a background daemon thread. Called once
    by main.py at startup so the key works regardless of system state."""
    thread = threading.Thread(target=_key_listener, daemon=True)
    thread.start()
