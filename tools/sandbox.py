"""Docker-based sandbox for applying patches and running a repo's test suite
in isolation.

Safety model (v1):
  - No bind mount. The repo is copied INTO the container over the Docker
    API (put_archive), so nothing the sandboxed process does can write back
    to the host filesystem -- there's no shared path for it to reach.
  - No network (`network_disabled=True`). A patch or test run can't exfiltrate
    data or pull anything down mid-run. Trade-off: the target repo's own
    dependencies must already be baked into the image (or vendored), since
    there's no `pip install` at run time. Fine for this step's sample repo;
    revisit when real target repos need arbitrary deps.
  - Resource caps: memory limit, single CPU, pids limit -- bounds a runaway
    test (fork bomb, infinite loop, memory leak).
  - Non-root user, all capabilities dropped, no-new-privileges.
  - Command timeout via coreutils `timeout`, not just resource caps.

Each `DockerSandbox` is a single throwaway container: create it, use it,
`.remove(force=True)` it. Nothing persists between runs.
"""
from __future__ import annotations

import io
import shlex
import tarfile
from dataclasses import dataclass
from pathlib import Path

import docker
from docker.errors import ImageNotFound, NotFound

IMAGE_TAG = "autonomous-dev-agent-sandbox:latest"
DOCKERFILE_DIR = Path(__file__).resolve().parent.parent / "docker"
CONTAINER_WORKDIR = "/workspace"


class SandboxError(Exception):
    """Raised for sandbox setup/lifecycle failures (not test failures)."""


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def build_image(client: docker.DockerClient | None = None, force: bool = False) -> str:
    """Build (or reuse) the sandbox image. Call once up front; cheap after."""
    client = client or docker.from_env()
    if not force:
        try:
            client.images.get(IMAGE_TAG)
            return IMAGE_TAG
        except ImageNotFound:
            pass
    client.images.build(
        path=str(DOCKERFILE_DIR),
        dockerfile="Dockerfile.sandbox",
        tag=IMAGE_TAG,
        rm=True,
    )
    return IMAGE_TAG


def _tar_bytes_of_dir(source_dir: Path) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for path in sorted(source_dir.rglob("*")):
            if ".git" in path.parts:
                continue
            tar.add(path, arcname=str(path.relative_to(source_dir)), recursive=False)
    return buf.getvalue()


def _tar_bytes_of_file(name: str, content: bytes) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=name)
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


class DockerSandbox:
    """Context manager wrapping one isolated, throwaway container.

    Usage:
        with DockerSandbox(repo_path) as sandbox:
            before = sandbox.run_tests()
            sandbox.apply_patch(diff_text)
            after = sandbox.run_tests()
    """

    def __init__(
        self,
        repo_path: Path | str,
        image: str = IMAGE_TAG,
        mem_limit: str = "512m",
        nano_cpus: int = 1_000_000_000,  # 1 CPU
        pids_limit: int = 256,
        timeout: int = 120,
        client: docker.DockerClient | None = None,
    ):
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.is_dir():
            raise SandboxError(f"repo path does not exist: {self.repo_path}")
        self.image = image
        self.mem_limit = mem_limit
        self.nano_cpus = nano_cpus
        self.pids_limit = pids_limit
        self.timeout = timeout
        self.client = client or docker.from_env()
        self._container = None

    def __enter__(self) -> "DockerSandbox":
        self._container = self.client.containers.run(
            self.image,
            command="sleep infinity",
            detach=True,
            network_disabled=True,
            mem_limit=self.mem_limit,
            nano_cpus=self.nano_cpus,
            pids_limit=self.pids_limit,
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            working_dir=CONTAINER_WORKDIR,
        )
        # Files copied in via put_archive keep the host's UID/GID, which
        # won't match the container's `sandbox` user -- fix ownership as
        # root before handing control back to the unprivileged user for
        # everything else.
        self._container.put_archive(CONTAINER_WORKDIR, _tar_bytes_of_dir(self.repo_path))
        self._exec_raw(f"chown -R sandbox:sandbox {CONTAINER_WORKDIR}", user="root")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._container is not None:
            try:
                self._container.remove(force=True)
            except NotFound:
                pass
            self._container = None

    def _exec_raw(self, cmd: str, user: str = "sandbox") -> ExecResult:
        exit_code, output = self._container.exec_run(
            ["sh", "-c", cmd],
            workdir=CONTAINER_WORKDIR,
            user=user,
            demux=True,
        )
        stdout, stderr = output
        return ExecResult(
            exit_code=exit_code if exit_code is not None else -1,
            stdout=(stdout or b"").decode(errors="replace"),
            stderr=(stderr or b"").decode(errors="replace"),
        )

    def run(self, cmd: str, timeout: int | None = None) -> ExecResult:
        """Run a shell command inside the sandbox as the unprivileged user."""
        if self._container is None:
            raise SandboxError("sandbox not started; use `with DockerSandbox(...)`")
        timeout = timeout or self.timeout
        wrapped = f"timeout {timeout}s sh -c {shlex.quote(cmd)}"
        result = self._exec_raw(wrapped)
        if result.exit_code == 124:
            result.timed_out = True
        return result

    def apply_patch(self, diff_text: str) -> ExecResult:
        """Copy a unified diff into the container and apply it with `git apply`."""
        if self._container is None:
            raise SandboxError("sandbox not started; use `with DockerSandbox(...)`")
        self._container.put_archive(
            "/tmp", _tar_bytes_of_file("patch.diff", diff_text.encode())
        )
        return self.run("git apply --whitespace=fix /tmp/patch.diff")

    def run_tests(self, test_cmd: str = "pytest -q") -> ExecResult:
        return self.run(test_cmd)
