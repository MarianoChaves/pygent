"""Run commands in a Docker container, falling back to local execution if needed."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Union

try:  # Docker may not be available (e.g. Windows without Docker)
    import docker  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    docker = None


class Runtime:
    """Executes commands in a Docker container or locally if Docker is unavailable."""

    def __init__(self, image: str | None = None, use_docker: bool | None = None) -> None:
        self.base_dir = Path(tempfile.mkdtemp(prefix="pygent_"))
        self.image = image or os.getenv("PYGENT_IMAGE", "python:3.12-slim")
        env_opt = os.getenv("PYGENT_USE_DOCKER")
        if use_docker is None:
            use_docker = (env_opt != "0") if env_opt is not None else True
        self._use_docker = bool(docker) and use_docker
        if self._use_docker:
            try:
                self.client = docker.from_env()
                self.container = self.client.containers.run(
                    self.image,
                    name=f"pygent-{uuid.uuid4().hex[:8]}",
                    command="sleep infinity",
                    volumes={str(self.base_dir): {"bind": "/workspace", "mode": "rw"}},
                    working_dir="/workspace",
                    detach=True,
                    tty=True,
                    network_disabled=True,
                    mem_limit="512m",
                    pids_limit=256,
                )
            except Exception:
                self._use_docker = False
        if not self._use_docker:
            self.client = None
            self.container = None

    # ---------------- public API ----------------
    def bash(self, cmd: str, timeout: int = 30) -> str:
        """Run a command in the container or locally and return the output."""
        if self._use_docker and self.container is not None:
            res = self.container.exec_run(
                cmd,
                workdir="/workspace",
                demux=True,
                tty=False,
                timeout=timeout,
            )
            stdout, stderr = (
                res.output if isinstance(res.output, tuple) else (res.output, b"")
            )
            return (stdout or b"").decode() + (stderr or b"").decode()
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=self.base_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.stdout + proc.stderr

    def write_file(self, rel_path: Union[str, Path], content: str) -> str:
        p = self.base_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Wrote {p.relative_to(self.base_dir)}"

    def cleanup(self) -> None:
        if self._use_docker and self.container is not None:
            try:
                self.container.kill()
            finally:
                self.container.remove(force=True)
        shutil.rmtree(self.base_dir, ignore_errors=True)
