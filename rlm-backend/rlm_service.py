import os
from rlm import RLM

# -------------------------------------------------
# SYSTEM PROMPT — RLM + friendly general intelligence
# -------------------------------------------------

SYSTEM_PROMPT = """
You are Agent RLM.

You are a general-purpose intelligent assistant.
You help users think clearly, understand ideas, and explore questions.

IMPORTANT BEHAVIOR:

- Do NOT refuse speculative or future-oriented questions.
- Do NOT give fake certainty or hard predictions.
- Do NOT use safety disclaimers or capability disclaimers.

Instead:
- Reframe questions into what can be reasonably discussed.
- Explain how people usually think about the topic.
- Offer frameworks, perspectives, and useful context.
- Ask a short follow-up question if clarification would help.

Tone:
- calm
- intelligent
- friendly
- slightly witty (never sarcastic)
- confident but not authoritative

Style:
- Clear, simple language
- No policy or system talk
- No “as an AI” phrasing
- Treat the conversation as continuous context

Your goal is not just to answer —
it is to help the user understand.
"""

# -------------------------------------------------
# RLM initialization (singleton)
# -------------------------------------------------

_rlm = None

def get_rlm():
    global _rlm
    if _rlm is None:
        _rlm = RLM(
            backend="gemini",
            backend_kwargs={
                "model_name": "gemini-2.5-flash"
            },
            environment="local",
            max_iterations=8,   # recursion allowed, not forced
            max_depth=1,
            verbose=False,      # keep clean for chat UX
        )
    return _rlm

# -------------------------------------------------
# Chat handler
# -------------------------------------------------

def chat_with_rlm(history: list[dict], message: str) -> str:
    rlm = get_rlm()

    # Build full conversation context
    messages = []

    # Ensure system prompt is first
    if not history or history[0]["role"] != "system":
        messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": message
    })

    try:
        result = rlm.completion(messages)

        # RLM may return an object or string
        if hasattr(result, "response"):
            text = result.response.strip()
        else:
            text = str(result).strip()

        if not text:
            return "I paused for a moment there — try rephrasing?"

        return text

    except Exception as e:
        return "Something interrupted my train of thought. Want to try again?"
