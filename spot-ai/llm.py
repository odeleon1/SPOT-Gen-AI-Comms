from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

# Conversation history — grows throughout an active session.
# Each entry is a ChatCompletionMessageParam with "role" and "content" keys.
# Sent in full to GPT-4o on every call so it has complete context.
_history: list[ChatCompletionMessageParam] = []


def chat(text: str) -> str:
    """
    Send the user's transcribed text to GPT-4o and return the reply.
    Appends both the user message and the assistant reply to history
    so future calls have full conversation context.
    Called by main.py on every active-state transcription.
    """
    _history.append({"role": "user", "content": text})

    system: ChatCompletionMessageParam = {"role": "system", "content": config.SYSTEM_PROMPT}
    messages: list[ChatCompletionMessageParam] = [system] + _history

    response = client.chat.completions.create(
        model=config.GPT_MODEL,
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