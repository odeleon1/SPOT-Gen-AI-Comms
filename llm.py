from openai import OpenAI

import config

# Grok's API is OpenAI-compatible, so the same client works — only the
# base_url and key change to point at xAI instead of OpenAI.
client = OpenAI(
    api_key = config.XAI_API_KEY,
    base_url = config.GROK_BASE_URL,
)

# Conversation history — grows throughout an active session.
# Sent in full to Grok on every call so it has complete context.
_history: list[dict] = []


def chat(text: str) -> str:
    """
    Send the user's transcribed text to Grok and return the reply.
    Appends both the user message and the assistant reply to history
    so future calls have full conversation context.
    Called by main.py on every active-state transcription.
    """
    _history.append({"role": "user", "content": text})

    messages = [{"role": "system", "content": config.SYSTEM_PROMPT}] + _history

    response = client.chat.completions.create(
        model=config.GROK_MODEL,
        messages=messages,
    )

    reply = (response.choices[0].message.content or "").strip()
    _history.append({"role": "assistant", "content": reply})

    return reply


def reset() -> None:
    """
    Clear the conversation history.
    Called by activation.py on deactivation if RESET_HISTORY_ON_DEACTIVATE
    is True in config.py.
    """
    _history.clear()