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


## Demo

https://github.com/user-attachments/assets/ae47fc8b-c84b-4323-9b29-719587a1a7f7

The full pipeline running end-to-end against a 7-issue benchmark: issue in,
plan produced, code written, tested inside an isolated Docker sandbox,
reviewed, and a final success-rate summary printed out.

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

Ran against a 7-issue benchmark spanning five toy repos: arithmetic,
string processing, list processing, dictionary merging/aggregation, and
range/off-by-one logic. Each issue is graded only against the specific
test verifying that fix, not the whole test suite, to avoid crediting or
penalizing the agent for unrelated bugs in the same file.

| Issue | Success | Attempts | Time |
|---|---|---|---|
| calculator_subtract | ✅ | 1 | 5.9s |
| calculator_divide_zero | ✅ | 2 | 7.1s |
| string_reverse_words | ✅ | 1 | 28.4s |
| list_unique_items | ✅ | 1 | 33.7s |
| dict_merge | ✅ | 1 | 30.9s |
| dict_word_frequency | ✅ | 1 | 28.3s |
| range_sum_off_by_one | ✅ | 3 | 65.0s |

**Success rate: 100% (n=7) — average 1.4 attempts to fix.**

Note: still a small benchmark (n=7), not representative of real-world
GitHub issue diversity or scale. `range_sum_off_by_one` took 3 attempts,
the most of any issue — off-by-one errors are a classic case where a
plausible-looking fix can still be subtly wrong, which is exactly the
kind of case the test-driven retry loop exists for.
