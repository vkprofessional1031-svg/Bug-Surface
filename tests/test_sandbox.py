"""Automated version of scripts/demo_sandbox.py, plus explicit isolation
checks. Skips (rather than fails) if no Docker daemon is reachable, so the
rest of the suite still runs in environments without Docker.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import docker
import pytest

from tools.file_ops import Workspace
from tools.sandbox import DockerSandbox, build_image

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_REPO = REPO_ROOT / "tests" / "fixtures" / "sample_repo"
FIX_PATCH = REPO_ROOT / "tests" / "fixtures" / "fix.patch"


def _docker_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_available(), reason="Docker daemon not reachable")


@pytest.fixture(scope="module", autouse=True)
def _ensure_image():
    build_image()


@pytest.fixture()
def workspace(tmp_path) -> Workspace:
    root = tmp_path / "sample_repo"
    shutil.copytree(SAMPLE_REPO, root)
    return Workspace(root)


@pytest.fixture()
def git_workspace(tmp_path) -> Workspace:
    """A workspace that is also a git repo, committed at the buggy baseline --
    what Workspace.diff()/apply_patch() need, and what a real cloned target
    repo would already be. Built fresh per-test rather than checked into the
    fixture directory, so the fixture itself stays a plain directory (a
    checked-in nested .git would look like a broken submodule to the outer
    project's own git repo).
    """
    root = tmp_path / "sample_repo"
    shutil.copytree(SAMPLE_REPO, root)
    run = lambda *args: __import__("subprocess").run(args, cwd=root, check=True, capture_output=True)
    run("git", "init", "-q")
    run("git", "-c", "user.email=agent@example.com", "-c", "user.name=agent", "add", "-A")
    run("git", "-c", "user.email=agent@example.com", "-c", "user.name=agent", "commit", "-q", "-m", "baseline")
    return Workspace(root)


def test_patch_apply_and_test_run(workspace: Workspace):
    diff_text = FIX_PATCH.read_text()

    with DockerSandbox(workspace.root) as sandbox:
        before = sandbox.run_tests()
        assert not before.ok
        assert "test_subtract" in before.stdout

        patch_result = sandbox.apply_patch(diff_text)
        assert patch_result.ok, patch_result.stderr

        after = sandbox.run_tests()
        assert after.ok, after.stdout + after.stderr

    # The container never had a bind mount, so the host checkout the patch
    # was staged from is untouched.
    assert "BUG" in SAMPLE_REPO.joinpath("calculator.py").read_text()


def test_sandbox_is_non_root(workspace: Workspace):
    with DockerSandbox(workspace.root) as sandbox:
        result = sandbox.run("id -u")
        assert result.stdout.strip() == "1000"


def test_sandbox_has_no_network(workspace: Workspace):
    with DockerSandbox(workspace.root) as sandbox:
        result = sandbox.run("wget -q -T 3 -O- https://example.com || echo BLOCKED")
        assert "BLOCKED" in result.stdout


def test_sandbox_drops_all_capabilities(workspace: Workspace):
    with DockerSandbox(workspace.root) as sandbox:
        result = sandbox.run("cat /proc/1/status | grep CapEff")
        assert "0000000000000000" in result.stdout


def test_sandbox_enforces_timeout(workspace: Workspace):
    with DockerSandbox(workspace.root) as sandbox:
        result = sandbox.run("sleep 5", timeout=2)
        assert result.timed_out
        assert result.exit_code == 124


def test_edit_diff_verify_round_trip(git_workspace: Workspace):
    """The realistic loop: agent edits a file in place, a diff is generated
    from the working tree, the working tree is reset (as if the edit never
    happened), and that diff alone is replayed and verified inside a fresh,
    isolated sandbox -- proving the diff produced by file_ops is what
    actually gets tested, not the in-memory edit.
    """
    fixed_source = git_workspace.read_file("calculator.py").replace(
        "    # BUG: should be a - b\n    return a + b", "    return a - b"
    )
    git_workspace.write_file("calculator.py", fixed_source)
    diff_text = git_workspace.diff()
    assert "-    return a + b" in diff_text
    assert "+    return a - b" in diff_text

    git_workspace.reset()
    assert "BUG" in git_workspace.read_file("calculator.py")

    with DockerSandbox(git_workspace.root) as sandbox:
        before = sandbox.run_tests()
        assert not before.ok

        patch_result = sandbox.apply_patch(diff_text)
        assert patch_result.ok, patch_result.stderr

        after = sandbox.run_tests()
        assert after.ok, after.stdout + after.stderr


def test_workspace_apply_patch_escapes_are_blocked(workspace: Workspace):
    from tools.file_ops import WorkspaceError

    with pytest.raises(WorkspaceError):
        workspace.read_file("../../etc/passwd")
    with pytest.raises(WorkspaceError):
        workspace.write_file("/etc/passwd", "pwned")
