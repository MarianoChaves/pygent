"""Run commands in a Docker container, falling back to local execution if needed."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Union

try:  # Docker may not be available (e.g. Windows without Docker)
    import docker  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    docker = None


class Runtime:
    """Executes commands in a Docker container or locally if Docker is unavailable."""

    def __init__(
        self,
        image: str | None = None,
        use_docker: bool | None = None,
        initial_files: list[str] | None = None,
    ) -> None:
        self.base_dir = Path(tempfile.mkdtemp(prefix="pygent_"))
        if initial_files is None:
            env_files = os.getenv("PYGENT_INIT_FILES")
            if env_files:
                initial_files = [f.strip() for f in env_files.split(os.pathsep) if f.strip()]
        self._initial_files = initial_files or []
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

        # populate workspace with initial files
        for fp in self._initial_files:
            src = Path(fp).expanduser()
            dest = self.base_dir / src.name
            if src.is_dir():
                shutil.copytree(src, dest, dirs_exist_ok=True)
            elif src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dest)

    # ---------------- public API ----------------
    def bash(self, cmd: str, timeout: int = 30) -> str:
        """Run a command and stream its output to the console.

        The returned value still contains the full captured output prefixed with
        the executed command. Output is printed line by line while the command
        runs so the user can see progress in real time.
        """
        prefix = f"$ {cmd}\n"
        print(prefix, end="")

        if self._use_docker and self.container is not None:
            try:
                res = self.container.exec_run(
                    cmd,
                    workdir="/workspace",
                    demux=True,
                    tty=False,
                    stdin=False,
                    timeout=timeout,
                    stream=True,
                )
                chunks = []
                for out in res.output:
                    stdout, stderr = (
                        out if isinstance(out, tuple) else (out, b"")
                    )
                    text = (stdout or b"").decode() + (stderr or b"").decode()
                    print(text, end="")
                    chunks.append(text)
                return prefix + "".join(chunks)
            except Exception as exc:
                err = f"[error] {exc}"
                print(err)
                return prefix + err

        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                stdin=subprocess.DEVNULL,
            )
            output_parts = []
            start = time.monotonic()
            assert proc.stdout is not None
            import select

            while True:
                if time.monotonic() - start > timeout:
                    proc.kill()
                    output_parts.append(f"[timeout after {timeout}s]")
                    print(f"[timeout after {timeout}s]")
                    break
                ready, _, _ = select.select([proc.stdout], [], [], 0.1)
                if ready:
                    line = proc.stdout.readline()
                    if line:
                        print(line, end="")
                        output_parts.append(line)
                    elif proc.poll() is not None:
                        break
                elif proc.poll() is not None:
                    break
            proc.wait()
            return prefix + "".join(output_parts)
        except Exception as exc:
            err = f"[error] {exc}"
            print(err)
            return prefix + err

    def write_file(self, path: Union[str, Path], content: str) -> str:
        p = self.base_dir / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {p.relative_to(self.base_dir)}"

    def read_file(self, path: Union[str, Path], binary: bool = False) -> str:
        """Return the contents of a file relative to the workspace."""

        p = self.base_dir / path
        if not p.exists():
            return f"file {p.relative_to(self.base_dir)} not found"
        data = p.read_bytes()
        if binary:
            import base64

            return base64.b64encode(data).decode()
        try:
            return data.decode()
        except UnicodeDecodeError:
            import base64

            return base64.b64encode(data).decode()

    def cleanup(self) -> None:
        if self._use_docker and self.container is not None:
            try:
                self.container.kill()
            finally:
                self.container.remove(force=True)
        shutil.rmtree(self.base_dir, ignore_errors=True)
