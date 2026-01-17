import os
from rlm import RLM

###  Integrate this script to front end chatbot system where it uses RLM


# ----------------------------
# 1) Configure Gemini key
# ----------------------------
# PowerShell:  $env:GEMINI_API_KEY="..."
# Or set it here (not recommended):
# os.environ["GEMINI_API_KEY"] = "YOUR_KEY"

# ----------------------------
# 2) Agent system prompt
# ----------------------------
SYSTEM_PROMPT = """
You are Agent RLM — a witty, friendly, intelligent assistant.

Core identity:
- You feel like a sharp autonomous agent, not a helpdesk bot.
- You are warm, curious, a little playful, and suggestive (offer good next steps).
- You avoid robotic phrasing and avoid sounding like documentation.

RLM "taste" (do NOT describe these mechanics to the user):
- You may recursively refine your answer internally.
- You may use the REPL environment to inspect context/state, draft, and tighten output.
- You may optionally make recursive sub-calls if needed for clarity or correctness.
- Most of the time, answer directly. Use recursion only when it helps.

Tool behavior:
- The REPL contains variables. You can store notes, drafts, and intermediate reasoning there.
- You have access to a helper function `llm_query(text)` inside the REPL to do sub-queries.
- Use the REPL sparingly. Prefer direct answers unless the question is complex.

Response style:
- Be concise by default.
- If the user asks for detail, go deeper.
- When unsure, say so and propose a quick way to verify.
- End with a helpful next question or suggestion when appropriate.

Hard rules:
- Do NOT summarize the user's message unless they asked for a summary.
- Do NOT respond with "The context is..." or meta descriptions.
- Do NOT reveal internal steps, REPL code, or recursion process.
"""

# ----------------------------
# 3) Create RLM instance
# ----------------------------
# Key settings to make recursion "optional":
# - Keep max_iterations modest (prevents long loops)
# - Keep verbose off for cleaner chat (turn on if debugging)
rlm = RLM(
    backend="gemini",
    backend_kwargs={"model_name": "gemini-2.5-flash"},
    environment="local",
    max_iterations=8,   # optional recursion, not a long research run
    max_depth=1,        # keep it simple
    verbose=False,      # chat UX; set True if you want to see REPL/tool steps
)

# ----------------------------
# 4) Chat loop
# ----------------------------
history = [{"role": "system", "content": SYSTEM_PROMPT}]

print("\nAgent RLM online. Type /exit to quit. Type /debug to toggle verbose.\n")

while True:
    user = input("You: ").strip()
    if not user:
        continue
    if user.lower() in ["/exit", "/quit"]:
        print("Agent RLM: Later. Stay sharp.")
        break
    if user.lower() == "/debug":
        rlm.verbose = not rlm.verbose
        print(f"(debug) verbose = {rlm.verbose}")
        continue

    history.append({"role": "user", "content": user})

    # IMPORTANT: pass the full message list (system + history)
    # No forced summarization prompt. The model decides if it uses REPL recursion.
    result = rlm.completion(history)

    assistant_text = result.response.strip() if hasattr(result, "response") else str(result).strip()
    if not assistant_text:
        assistant_text = "…I blanked for a second. Try asking that a different way?"

    print(f"\nAgent RLM: {assistant_text}\n")

    history.append({"role": "assistant", "content": assistant_text})
