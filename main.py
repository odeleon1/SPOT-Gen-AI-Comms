import time

import config
import stt
import llm
import tts
import activation


def _run_idle() -> None:
    # Record a short clip and check it for the activation phrase. Anything that
    # is not the wake phrase is discarded.
    text = stt.listen_short()
    if text:
        print(f'[IDLE] heard: "{text}"')
    activation.check(text)


def _run_active() -> None:
    # Capture a full utterance. check() runs first so a deactivation command is
    # caught before it reaches the LLM; we re-check state before replying.
    text = stt.listen()
    if not text:
        return

    print(f'[ACTIVE] User: "{text}"')
    activation.check(text)

    if not activation.is_active():
        return

    reply = llm.chat(text)
    print(f'[ACTIVE] SPOT: "{reply}"')
    tts.speak(reply)


def main() -> None:
    activation.start_key_listener()

    print("SPOT AI Comms started.")
    print(f'Say "{config.ACTIVATION_PHRASE}" or press '
          f'{config.MANUAL_TOGGLE_KEY.upper()} to activate.')
    print("Press Ctrl+C to quit.\n")

    try:
        while True:
            if activation.is_active():
                _run_active()
            else:
                _run_idle()
            time.sleep(0.1)   # small pause so the idle loop does not spin too hard
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
