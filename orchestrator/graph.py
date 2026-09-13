"""Ties planner -> coder -> sandbox test -> reviewer -> retry-on-failure
together, with a memory store that retrieves similar past fixes before
coding and saves new approved fixes afterward."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from tools.file_ops import Workspace
from tools.sandbox import DockerSandbox, build_image
from agents.planner import run_planner
from agents.coder import run_coder
from agents.reviewer import run_reviewer
from memory.store import store_fix, retrieve_similar


def _make_git_copy(source_dir: Path) -> Path:
    tmp_dir = Path(tempfile.mkdtemp(prefix="agent_run_"))
    shutil.copytree(source_dir, tmp_dir, dirs_exist_ok=True)
    subprocess.run(["git", "init"], cwd=tmp_dir, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=agent@local", "-c", "user.name=agent",
         "commit", "-m", "baseline"],
        cwd=tmp_dir, check=True, capture_output=True,
    )
    return tmp_dir


def run_pipeline(
    repo_path: str,
    issue_text: str,
    target_files: list[str],
    issue_name: str,
    test_cmd: str = "pytest -q",
    max_attempts: int = 5,
) -> dict:
    build_image()

    working_copy = _make_git_copy(Path(repo_path))
    ws = Workspace(working_copy)

    file_contents = {f: ws.read_file(f) for f in target_files}
    plan = run_planner(issue_text, file_contents)

    memory_lessons = retrieve_similar(issue_text)

    feedback = None
    for attempt in range(1, max_attempts + 1):
        coder_output = run_coder(plan, file_contents, test_feedback=feedback, memory_lessons=memory_lessons)
        for change in coder_output.changes:
            ws.write_file(change.file_path, change.new_content)

        with DockerSandbox(ws.root) as sandbox:
            result = sandbox.run_tests(test_cmd)

        if not result.ok:
            feedback = f"Tests failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            ws.reset()
            continue

        diff_text = ws.diff()
        review = run_reviewer(issue_text, diff_text)

        if review.approved:
            store_fix(issue_text, diff_text, review.reasoning, issue_name)
            return {
                "success": True,
                "attempts": attempt,
                "diff": diff_text,
                "plan": plan,
                "review": review,
                "used_memory": len(memory_lessons) > 0,
            }

        feedback = (
            f"Tests passed, but code review rejected this fix.\n"
            f"Reasoning: {review.reasoning}\n"
            f"Concerns: {'; '.join(review.concerns)}"
        )
        ws.reset()

    return {
        "success": False,
        "attempts": max_attempts,
        "last_feedback": feedback,
        "plan": plan,
    }
