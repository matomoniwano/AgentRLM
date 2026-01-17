from rlm import RLM
from prompt_builder import load_character_prompt

# Singleton
_rlm = None
_SYSTEM_PROMPT = None


def get_rlm():
    global _rlm, _SYSTEM_PROMPT

    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = load_character_prompt()

    if _rlm is None:
        _rlm = RLM(
            backend="gemini",
            backend_kwargs={
                "model_name": "gemini-2.5-flash"
            },
            environment="local",
            max_iterations=8,   # optional recursion
            max_depth=1,
            verbose=False,
        )

    return _rlm, _SYSTEM_PROMPT


def chat_with_rlm(history: list[dict], message: str) -> str:
    rlm, system_prompt = get_rlm()

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    result = rlm.completion(messages)

    if hasattr(result, "response"):
        return result.response.strip()

    return str(result).strip()
