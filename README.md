# Autonomous Dev Agent

An AI agent system that autonomously fixes software bugs — from a plain-English
issue description to a tested, reviewed code patch — using a multi-agent pipeline
with self-correction and persistent memory.

## Why this exists

Most "AI coding demo" projects are a single LLM call that writes code once and
hopes for the best. This project is different: it's built around a **feedback
loop**. If a fix breaks a test, the agent sees the failure and tries again
(up to a capped number of retries) instead of giving up or silently failing.
A separate reviewer agent then checks the diff for things tests don't catch —
style, missed edge cases, security smells — before anything is considered done.

## Architecture

1. **Planner agent** — takes an issue description, produces a structured plan
   (root cause hypothesis, files to touch, ordered subtasks)
2. **Coder agent** — reads relevant files and writes a patch, using tool calls
   (read_file, write_file, run_tests)
3. **Test runner** — runs the target repo's own test suite inside an isolated
   Docker sandbox; failures are fed back to the coder agent for another attempt
4. **Reviewer agent** — critiques the passing diff against a rubric before
   it's considered mergeable
5. **Memory store** — a vector database of past fixes and human feedback,
   retrieved and injected into future prompts so the agent improves over time

## Status

🚧 Actively in development. Currently built:

- [x] **Sandbox + tool layer** — Dockerized, network-disabled, capability-dropped
      execution environment with file read/write tools (`tools/sandbox.py`,
      `tools/file_ops.py`), fully tested (7 passing tests)
- [x] **Planner agent** — Groq (`openai/gpt-oss-120b`) + Instructor for
      schema-validated structured planning output (`agents/planner.py`)
- [ ] Coder agent
- [ ] Test-driven retry loop
- [ ] Reviewer agent
- [ ] Memory store (vector DB + retrieval)
- [ ] Evaluation benchmark against real bugs

## Tech stack

- **LLM inference:** Groq (Llama/GPT-OSS models)
- **Structured output:** Pydantic + Instructor
- **Sandboxing:** Docker
- **Memory/retrieval:** Chroma + sentence-transformers
- **Orchestration:** hand-rolled Python state machine (deliberately not
  LangGraph/AutoGen — see notes below)
- **Dashboard:** Streamlit (planned)

## Design notes

**Why no agent framework?** Orchestration is handled with a plain Python
state machine rather than LangGraph, AutoGen, or CrewAI. This is a deliberate
choice: it keeps every step of the plan → code → test → review loop fully
visible and debuggable, rather than hidden behind framework abstractions.

**Why Docker with no bind mount?** The sandbox copies the target repo into
the container rather than sharing a filesystem path with the host, so nothing
the agent does inside the container can touch the host machine, even if the
generated code is buggy or malicious.

## Running it locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# add your Groq API key to .env as GROQ_API_KEY=...
python -m scripts.demo_planner
```
