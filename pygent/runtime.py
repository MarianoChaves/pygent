"""Explicit Docker or trusted local command execution."""
from __future__ import annotations

import os
import shutil
import subprocess
import uuid
import threading
import math
import signal
from pathlib import Path
from typing import Union, Optional, Callable

try:  # Docker may not be available (e.g. Windows without Docker)
    import docker  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    docker = None


class Runtime:
    """Executes commands in Docker, or locally when explicitly requested.

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
        self.base_dir = self.base_dir.resolve()
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
        self._use_docker = use_docker
        self.client = None
        self.container = None
        if use_docker and (docker is None or not hasattr(docker, "from_env")):
            if not self._persistent:
                shutil.rmtree(self.base_dir, ignore_errors=True)
            raise RuntimeError("Docker is required. Install pygent[docker] and start Docker, "
                               "or explicitly select use_docker=False for trusted local execution.")
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
            except Exception as exc:
                if self.client is not None:
                    self.client.close()
                if not self._persistent:
                    shutil.rmtree(self.base_dir, ignore_errors=True)
                raise RuntimeError("Docker startup failed; local execution was not enabled") from exc
        if not self._use_docker:
            self.client = None
            self.container = None

        try:
            # populate workspace with initial files
            for fp in self._initial_files:
                src = Path(fp).expanduser()
                dest = self.base_dir / src.name
                self.check_copy_tree(src)
                self.check_copy_tree(dest)
                if src.is_dir():
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                elif src.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src, dest)

        except Exception:
            self.cleanup()
            raise

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
    def bash(
        self, cmd: str, timeout: float = 600,
        stream: Optional[Callable[[str], None]] = None,
        max_output_chars: int = 64_000,
    ) -> str:
        """Run a shell command with bounded capture and an execution timeout.

        Output is streamed in chunks. On POSIX the local process group is killed
        on timeout (including ordinary shell children). Docker images must provide
        ``sh`` and GNU ``timeout``. Local mode is trusted execution, not a sandbox.
        """
        if not math.isfinite(timeout) or timeout < 0:
            raise ValueError("timeout must be finite and nonnegative")
        if not isinstance(max_output_chars, int) or max_output_chars < 1:
            raise ValueError("max_output_chars must be a positive integer")
        if timeout == 0:
            return f"$ {cmd}\n[timeout after 0s]"
        tokens = cmd.split()
        if tokens:
            if Path(tokens[0]).name in self.banned_commands:
                return f"$ {cmd}\n[error] command '{Path(tokens[0]).name}' disabled"
            for token in tokens:
                if Path(token).name in self.banned_apps:
                    return f"$ {cmd}\n[error] application '{Path(token).name}' disabled"
        parts: list[str] = []
        captured = 0
        truncated = False

        def emit(text: str) -> None:
            nonlocal captured, truncated
            remaining = max_output_chars - captured
            chunk = text[:remaining]
            if chunk:
                parts.append(chunk)
                captured += len(chunk)
                if stream:
                    stream(chunk)
            if len(text) > remaining and not truncated:
                truncated = True
                parts.append("\n[output truncated]\n")
                if stream:
                    stream("\n[output truncated]\n")

        emit(f"$ {cmd}\n")
        if self._use_docker and self.container is not None:
            try:
                result = self.container.exec_run(
                    ["timeout", "--signal=KILL", str(timeout), "sh", "-lc", cmd],
                    workdir="/workspace", stream=True, tty=False, stdin=False,
                )
                for chunk in result.output:
                    emit(chunk.decode("utf-8", errors="replace"))
            except Exception as exc:
                emit(f"[error] {exc}")
            return "".join(parts)

        proc = subprocess.Popen(
            cmd, shell=True, cwd=self.base_dir, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            start_new_session=(os.name == "posix"),
        )
        reader_errors: list[Exception] = []

        def read_output() -> None:
            import codecs
            decoder = codecs.getincrementaldecoder("utf-8")("replace")
            try:
                assert proc.stdout is not None
                while True:
                    chunk = os.read(proc.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    emit(decoder.decode(chunk))
                emit(decoder.decode(b"", final=True))
            except Exception as exc:
                reader_errors.append(exc)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Also remove background descendants after their parent shell exits.
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif proc.poll() is None:
                proc.kill()
            proc.wait()
            reader.join(timeout=2)
            if not reader.is_alive() and proc.stdout is not None:
                proc.stdout.close()
        if reader_errors:
            raise reader_errors[0]
        if timed_out:
            emit(f"[timeout after {timeout}s]\n")
        return "".join(parts)

    def resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve a workspace-relative path, rejecting escapes and symlinks.

        This is a file API boundary, not an OS sandbox against concurrent hostile
        filesystem mutation. Shell commands require separate OS isolation.
        """
        value = Path(path)
        if value.is_absolute():
            raise ValueError("workspace paths must be relative")
        candidate = self.base_dir / value
        if candidate.is_symlink() or any(parent.is_symlink() for parent in candidate.parents):
            raise ValueError("symlinks are not allowed in workspace paths")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.base_dir):
            raise ValueError("path escapes the workspace")
        return resolved

    @staticmethod
    def check_copy_tree(path: Path) -> None:
        """Reject symlinks before a recursive copy, including nested entries."""
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("symlinks are not allowed in copied paths")
        if path.is_dir():
            for root, directories, files in os.walk(path):
                for name in directories + files:
                    if (Path(root) / name).is_symlink():
                        raise ValueError("symlinks are not allowed in copied directories")

    def __enter__(self) -> Runtime:
        return self

    def __exit__(self, *exc: object) -> None:
        self.cleanup()

    def write_file(self, path: Union[str, Path], content: str) -> str:
        p = self.resolve_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {p.relative_to(self.base_dir)}"

    def read_file(self, path: Union[str, Path], binary: bool = False) -> str:
        """Return the contents of a file relative to the workspace."""

        p = self.resolve_path(path)
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
        target = self.resolve_path(Path(dest) if dest else src_path.name)
        self.check_copy_tree(src_path)
        self.check_copy_tree(target)
        if src_path.is_dir():
            shutil.copytree(src_path, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, target)
        return f"Uploaded {target.relative_to(self.base_dir)}"

    def export_file(self, path: Union[str, Path], dest: Union[str, Path]) -> str:
        """Copy a file or directory from the workspace to a local path."""

        src = self.resolve_path(path)
        if not src.exists():
            return f"file {path} not found"
        dest_path = Path(dest).expanduser()
        self.check_copy_tree(src)
        self.check_copy_tree(dest_path)
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
                self.container = None
        if self.client is not None:
            self.client.close()
            self.client = None
        if not self._persistent:
            shutil.rmtree(self.base_dir, ignore_errors=True)
