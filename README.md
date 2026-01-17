![banner](link here)
# Agent RLM

**Agent RLM** is the first Recursive Language Model (RLM)–based agent built on Solana.

It is inspired by the *Recursive Language Models* paper by **Alex Zhang and the MIT CSAIL / OASYS team**, and is built on top of a fork of the official RLM repository:
👉 https://github.com/alexzhang13/rlm

This project adapts the core RLM inference ideas into a **lighter, agent-style conversational system**, designed for real-time interaction rather than research benchmarking.

---

## What is Agent RLM?

Agent RLM is not a standard chatbot.

It is designed around the RLM idea:
- context treated as a mutable state
- recursive internal refinement before responding
- convergence over verbosity

From the outside, it behaves like a calm, capable AI agent.  
Internally, it refines before it speaks.

---

## About Recursive Language Models (RLMs)

Recursive Language Models (RLMs) are an inference paradigm that allows language models to:
- programmatically inspect large contexts
- decompose inputs
- recursively call themselves
- avoid context degradation (“context rot”)

The original research and open-source framework were introduced by **Alex Zhang et al. (MIT CSAIL)**.

📄 Paper: https://arxiv.org/abs/2512.24601  
📝 Blog: https://alexzhang13.github.io/blog/2025/rlm/  
🧠 Original Repo: https://github.com/alexzhang13/rlm  

---

## This Repository

This repo contains:
- a forked and adapted version of the original RLM framework
- a lightweight conversational agent implementation
- adjustments focused on real-time chat and deployment

It is **not** a drop-in replacement for the research codebase.  
It is an **agent-oriented adaptation**.

---

## Links

- 🌐 Website: https://rlm.codes  
- 🐦 Twitter / X: https://x.com/AgentRLM  

---

## Credits

Recursive Language Models were introduced by:

**Alex L. Zhang**, **Tim Kraska**, **Omar Khattab**  
MIT CSAIL / OASYS Lab

If you are interested in the full research implementation, benchmarks, or sandboxed REPL environments, please refer to the original repository and paper.

---

Agent RLM is an experiment in bringing recursive inference out of papers and into agents.
