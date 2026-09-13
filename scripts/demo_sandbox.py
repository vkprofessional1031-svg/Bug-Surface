"""End-to-end smoke test for the sandbox layer. No LLM involved -- this just
proves the mechanics: a patch gets applied and a test suite gets run inside
an isolated container, safely.

Flow:
  1. Copy the buggy sample repo (tests/fixtures/sample_repo) into a scratch
     workspace.
  2. Read the pre-made fix (tests/fixtures/fix.patch) -- standing in for a
     diff the coder agent would produce via Workspace.diff() after editing
     files with Workspace.write_file().
  3. Build the sandbox image (cached after the first run).
  4. Start an isolated container (no bind mount, no network, resource-capped,
     non-root), copy the repo into it, run the test suite -- expect failure.
  5. Apply the patch inside the container, re-run the test suite -- expect
     pass.

Run: python scripts/demo_sandbox.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.file_ops import Workspace
from tools.sandbox import DockerSandbox, build_image

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_REPO = REPO_ROOT / "tests" / "fixtures" / "sample_repo"
FIX_PATCH = REPO_ROOT / "tests" / "fixtures" / "fix.patch"


def banner(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    diff_text = FIX_PATCH.read_text()

    with tempfile.TemporaryDirectory(prefix="sandbox-demo-") as tmp:
        workspace_root = Path(tmp) / "sample_repo"
        shutil.copytree(SAMPLE_REPO, workspace_root)
        workspace = Workspace(workspace_root)

        banner("Workspace contents (file_ops.Workspace.list_files)")
        for f in workspace.list_files():
            print(f" - {f}")

        banner("Building sandbox image (cached after first run)")
        image = build_image()
        print(f"image ready: {image}")

        with DockerSandbox(workspace_root) as sandbox:
            banner("Running tests BEFORE the patch (expect failure)")
            before = sandbox.run_tests()
            print(before.stdout)
            print(before.stderr)
            if before.ok:
                print("UNEXPECTED: tests passed before the patch was applied")
                return 1

            banner("Applying patch inside the isolated container")
            patch_result = sandbox.apply_patch(diff_text)
            print(patch_result.stdout)
            print(patch_result.stderr)
            if not patch_result.ok:
                print("Patch failed to apply")
                return 1

            banner("Running tests AFTER the patch (expect pass)")
            after = sandbox.run_tests()
            print(after.stdout)
            print(after.stderr)
            if not after.ok:
                print("Tests still failing after patch")
                return 1

        banner("Confirming host checkout is untouched")
        print("still buggy on disk:", SAMPLE_REPO.joinpath("calculator.py").read_text().count("BUG"))

    print("\nSUCCESS: patch applied and verified inside an isolated container.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
