"""Run commands in a Docker container, falling back to local execution if needed."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Union, Optional

try:  # Docker may not be available (e.g. Windows without Docker)
    import docker  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    docker = None


class Runtime:
    """Executes commands in a Docker container or locally if Docker is unavailable.

    If ``workspace`` or the environment variable ``PYGENT_WORKSPACE`` is set,
    the given directory is used as the base workspace and kept across sessions.
    """

    def __init__(
        self,
        image: Optional[str] = None,
        use_docker: Optional[bool] = None,
        initial_files: Optional[list[str]] = None,
        workspace: Optional[Union[str, Path]] = None,
        banned_commands: Optional[list[str]] = None,
        banned_apps: Optional[list[str]] = None,
    ) -> None:
        """Create a new execution runtime.

        ``banned_commands`` and ``banned_apps`` can be used to restrict what
        can be run. Environment variables ``PYGENT_BANNED_COMMANDS`` and
        ``PYGENT_BANNED_APPS`` extend these lists using ``os.pathsep`` as the
        delimiter.
        """
        env_ws = os.getenv("PYGENT_WORKSPACE")
        if workspace is None and env_ws:
            workspace = env_ws
        if workspace is None:
            self.base_dir = Path.cwd() / f"agent_{uuid.uuid4().hex[:8]}"
            self._persistent = False
        else:
            self.base_dir = Path(workspace).expanduser()
            self._persistent = True
        self.base_dir.mkdir(parents=True, exist_ok=True)
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

        env_banned_cmds = os.getenv("PYGENT_BANNED_COMMANDS")
        env_banned_apps = os.getenv("PYGENT_BANNED_APPS")
        self.banned_commands = set(banned_commands or [])
        if env_banned_cmds:
            self.banned_commands.update(c.strip() for c in env_banned_cmds.split(os.pathsep) if c.strip())
        self.banned_apps = set(banned_apps or [])
        if env_banned_apps:
            self.banned_apps.update(a.strip() for a in env_banned_apps.split(os.pathsep) if a.strip())

    @property
    def use_docker(self) -> bool:
        """Return ``True`` if commands run inside a Docker container."""
        return self._use_docker

    # ---------------- public API ----------------
    def bash(self, cmd: str, timeout: int = 600) -> str:
        """Run a command in the container or locally and return the output.

        The executed command is always included in the returned string so the
        caller can display what was run.
        """
        tokens = cmd.split()
        if tokens:
            from pathlib import Path

            if Path(tokens[0]).name in self.banned_commands:
                return f"$ {cmd}\n[error] command '{tokens[0]}' disabled"
            for t in tokens:
                if Path(t).name in self.banned_apps:
                    return f"$ {cmd}\n[error] application '{Path(t).name}' disabled"
        if self._use_docker and self.container is not None:
            try:
                res = self.container.exec_run(
                    cmd,
                    workdir="/workspace",
                    demux=True,
                    tty=False,
                    stdin=False,
                    timeout=timeout,
                )
                stdout, stderr = (
                    res.output if isinstance(res.output, tuple) else (res.output, b"")
                )
                output = (stdout or b"").decode() + (stderr or b"").decode()
                return f"$ {cmd}\n{output}"
            except Exception as exc:
                return f"$ {cmd}\n[error] {exc}"
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
            )
            return f"$ {cmd}\n{proc.stdout + proc.stderr}"
        except subprocess.TimeoutExpired:
            return f"$ {cmd}\n[timeout after {timeout}s]"
        except Exception as exc:
            return f"$ {cmd}\n[error] {exc}"

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

    def upload_file(self, src: Union[str, Path], dest: Optional[Union[str, Path]] = None) -> str:
        """Copy a local file or directory into the workspace."""

        src_path = Path(src).expanduser()
        if not src_path.exists():
            return f"file {src} not found"
        target = self.base_dir / (Path(dest) if dest else src_path.name)
        if src_path.is_dir():
            shutil.copytree(src_path, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, target)
        return f"Uploaded {target.relative_to(self.base_dir)}"

    def export_file(self, path: Union[str, Path], dest: Union[str, Path]) -> str:
        """Copy a file or directory from the workspace to a local path."""

        src = self.base_dir / path
        if not src.exists():
            return f"file {path} not found"
        dest_path = Path(dest).expanduser()
        if src.is_dir():
            shutil.copytree(src, dest_path, dirs_exist_ok=True)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dest_path)
        return f"Exported {src.relative_to(self.base_dir)}"

    def cleanup(self) -> None:
        if self._use_docker and self.container is not None:
            try:
                self.container.kill()
            finally:
                self.container.remove(force=True)
        if not self._persistent:
            shutil.rmtree(self.base_dir, ignore_errors=True)
