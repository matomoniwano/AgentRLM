import json
from pathlib import Path

CHARACTER_PATH = Path(__file__).parent / "character.json"


def load_character_prompt() -> str:
    """
    Convert Eliza character.json into a SYSTEM PROMPT string
    that RLM can reason under.
    """
    data = json.loads(CHARACTER_PATH.read_text(encoding="utf-8"))

    sections = []

    # Identity
    sections.append(f"You are {data.get('name')} (@{data.get('username')}).")
    sections.append(data.get("bio", ""))

    # Core system description
    if "system" in data:
        sections.append(data["system"])

    # Traits
    adjectives = data.get("adjectives", [])
    if adjectives:
        sections.append(
            "Personality traits:\n- " + "\n- ".join(adjectives)
        )

    # Topics
    topics = data.get("topics", [])
    if topics:
        sections.append(
            "Topics of interest:\n- " + "\n- ".join(topics)
        )

    # Chat style
    chat_style = data.get("style", {}).get("chat", [])
    if chat_style:
        sections.append(
            "Chat style guidelines:\n- " + "\n- ".join(chat_style)
        )

    # Hard rules
    sections.append(
        """
Hard constraints:
- Do NOT mention system prompts, internal reasoning, or tools
- Do NOT use disclaimers like “as an AI”
- Do NOT refuse speculative questions
- Be helpful even when certainty is impossible
- Treat conversation as continuous context
""".strip()
    )

    return "\n\n".join(s.strip() for s in sections if s.strip())
