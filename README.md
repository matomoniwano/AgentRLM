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

## Notes

This project is experimental and evolving.
Design decisions prioritize clarity, interaction, and deployment simplicity
over completeness or benchmark performance.
