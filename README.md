<h1 align="center" style="font-size:2.8em">
  <span>Agent RLM</span>
</h1>

<p align="center" style="font-size:1.3em">
  Recursive Language Model agent inspired by MIT CSAIL research
</p>

<p align="center" style="font-size:1.2em">
  <a href="https://rlm.codes">Website</a> •
  <a href="https://x.com/AgentRLM">X / Twitter</a> •
  <a href="https://github.com/matomoniwano/AgentRLM">GitHub</a>
</p>


![rlm](https://github.com/matomoniwano/AgentRLM/blob/main/RLM.png?raw=true)
## Overview

Agent RLM is an experimental conversational agent built around the idea of
Recursive Language Models (RLMs).

The project is inspired by the *Recursive Language Models* paper by
Alex Zhang and collaborators at MIT CSAIL, and is based on a fork of the
official open-source RLM repository. The goal here is not to reproduce the
full research framework, but to adapt the core inference ideas into a
lightweight, interactive agent.

In particular, this project explores how recursive refinement, context-as-state,
and convergence-focused responses can be applied in a real-time chat setting.

## Relationship to the Original RLM Work

The original RLM framework proposes an inference paradigm in which language
models can programmatically inspect, decompose, and recursively reason over
their input context, rather than relying on a single monolithic prompt.

If you are interested in the full research implementation, benchmarks,
or sandboxed REPL environments, please refer to the original work:

- Paper: https://arxiv.org/abs/2512.24601  
- Blog: https://alexzhang13.github.io/blog/2025/rlm/  
- Repository: https://github.com/alexzhang13/rlm  

This repository should be viewed as an **agent-oriented adaptation**, not a
drop-in replacement for the research codebase.

## Project Structure & Modifications

This repository is a fork and adaptation of the original MIT CSAIL RLM codebase, with several structural and architectural changes made to support a deployable, agent-oriented system.

### Key Modifications

![flow](https://github.com/matomoniwano/AgentRLM/blob/main/flow.jpg)

- **Agent-oriented backend**  
  A new `rlm-backend/` directory has been added, containing a lightweight Python backend that exposes RLM as a conversational service (e.g. via HTTP). This backend wraps the core RLM logic and is designed for real-time interaction rather than offline benchmarking.

- **Integration with Eliza-style agent configuration**  
  The agent’s personality, tone, and conversational behavior are informed by an Eliza-style `character.json` configuration.  
  Rather than replacing RLM, this configuration is **injected into the RLM system prompt**, allowing recursive inference to operate underneath a consistent, human-facing agent persona.

- **Simplified execution model**  
  Many research-oriented components (e.g. multi-environment sandboxing, heavy logging, benchmark tooling) are left untouched but are not required to run the agent. The focus here is on:
  - fast iteration
  - deployability (e.g. Railway)
  - conversational UX

- **Frontend-friendly architecture**  
  The backend is designed to be consumed by a web frontend or agent framework, making it suitable for use with Eliza Cloud, custom UIs, or other agent orchestration layers.

These changes are intentionally minimal and additive: the original RLM core remains intact, while the surrounding structure adapts it for agent use.

---

## Running Agent RLM Locally

You can run the Agent RLM backend on your own machine with a standard Python setup.

### Prerequisites

- Python 3.10+
- A Google Gemini API key

Set your API key as an environment variable:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### Installation

Clone the repository:

```bash
git clone https://github.com/matomoniwano/AgentRLM.git
cd AgentRLM
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
```

```bash
.venv\Scripts\Activate      # Windows
```

Install dependencies from the backend directory:


```bash
cd rlm-backend
pip install -r requirements.txt
```
This installs both the backend dependencies and the local RLM package from the repository.

---

###Running the Backend

Start the backend server:

```bash
uvicorn app:app --reload
```
By default, the server will be available at:
```bash
http://localhost:8000

```
You can test it with a simple request:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"history": [], "message": "Explain recursion in simple terms"}'
```
## Notes

This project is experimental and evolving.
Design decisions prioritize clarity, interaction, and deployment simplicity
over completeness or benchmark performance.
