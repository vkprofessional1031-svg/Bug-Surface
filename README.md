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
- [x] **Coder agent** — Groq + Instructor (JSON mode) for structured code fixes (`agents/coder.py`)
- [x] **Test-driven retry loop** — coder retries on test failure using real test output as feedback, verified with a controlled failure/recovery case
- [x] **Reviewer agent** — adversarial post-test review, verified with substantive real approve/reject reasoning (`agents/reviewer.py`)
- [x] **Evaluation benchmark** — 4 diverse bugs across 3 toy repos, 100% success rate, 1.5 avg attempts (`eval/`)
- [x] **Memory store** — Chroma + sentence-transformers, retrieves similar past fixes and injects them into the coder's prompt; verified that a new but similar bug (`modulo` by zero) reused the exact fix pattern from an earlier stored lesson (`divide` by zero) (`memory/store.py`)
- [ ] Dashboard

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


## Evaluation results

Ran against a 4-issue benchmark spanning three toy repos (arithmetic,
string processing, list processing bugs). Each issue is graded only
against the specific test verifying that fix (not the whole test suite),
to avoid crediting or penalizing the agent for unrelated bugs in the
same file -- an earlier version of this benchmark ran the full test
file per issue and showed misleading results as a result.

| Issue | Success | Attempts | Time |
|---|---|---|---|
| calculator_subtract | ✅ | 1 | 4.0s |
| calculator_divide_zero | ✅ | 2 | 6.8s |
| string_reverse_words | ✅ | 1 | 7.7s |
| list_unique_items | ✅ | 2 | 36.7s |

**Success rate: 100% (n=4) — average 1.5 attempts to fix.**

Note: small benchmark (n=4), not yet representative of real-world GitHub
issue diversity. `list_unique_items` consistently takes longer and more
attempts than the others -- likely because it requires reasoning about
an invariant (order preservation during deduplication) rather than a
single mechanical operator swap, an early signal that fix difficulty
correlates with reasoning complexity, not just code size.
