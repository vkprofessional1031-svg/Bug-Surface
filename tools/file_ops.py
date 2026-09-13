"""Root-scoped file operations backing the coder agent's read_file / write_file
tools.

Everything here operates on a `Workspace`: a directory the agent is allowed
to touch. Every path argument is resolved relative to that root and checked
to make sure it can't escape it (no `../..`, no absolute paths, no symlink
tricks) -- this is the boundary that keeps a hallucinated or adversarial
file path from writing outside the checkout the agent is supposed to be
editing.

This module never runs untrusted *code* -- it only reads/writes text and
shells out to `git` for diffing/patching/resetting. Running the resulting
patch and the repo's test suite happens in tools/sandbox.py instead, inside
an isolated container.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class WorkspaceError(Exception):
    """Raised for unsafe or invalid workspace operations."""


@dataclass
class PatchResult:
    applied: bool
    stdout: str
    stderr: str


class Workspace:
    """A filesystem sandbox rooted at a single directory (a repo checkout)."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise WorkspaceError(f"workspace root does not exist: {self.root}")

    def _resolve(self, relative_path: str) -> Path:
        if Path(relative_path).is_absolute():
            raise WorkspaceError(f"absolute paths are not allowed: {relative_path!r}")
        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            raise WorkspaceError(
                f"path escapes workspace root: {relative_path!r}"
            ) from None
        return candidate

    def read_file(self, relative_path: str) -> str:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise WorkspaceError(f"not a file: {relative_path!r}")
        return path.read_text()

    def write_file(self, relative_path: str, content: str) -> None:
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def list_files(self, pattern: str = "**/*") -> list[str]:
        return sorted(
            str(p.relative_to(self.root))
            for p in self.root.glob(pattern)
            if p.is_file() and ".git" not in p.parts
        )

    def diff(self) -> str:
        """Unified diff of the current working tree against HEAD.

        Requires `root` to be a git repo -- this is how the coder agent's
        in-place edits get turned into a patch to hand to the sandbox.
        """
        result = subprocess.run(
            ["git", "diff", "--no-color"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise WorkspaceError(f"git diff failed: {result.stderr}")
        return result.stdout

    def apply_patch(self, diff_text: str) -> PatchResult:
        """Apply a unified diff to this workspace via `git apply`."""
        result = subprocess.run(
            ["git", "apply", "--whitespace=fix", "-"],
            cwd=self.root,
            input=diff_text,
            capture_output=True,
            text=True,
        )
        return PatchResult(
            applied=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def reset(self) -> None:
        """Discard all working-tree changes, restoring the last commit."""
        subprocess.run(["git", "checkout", "--", "."], cwd=self.root, check=True)
        subprocess.run(["git", "clean", "-fd"], cwd=self.root, check=True)
