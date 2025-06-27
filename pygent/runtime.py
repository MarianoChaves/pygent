"""Isola as execuções num container Docker efêmero."""
from __future__ import annotations

import os
import shutil
import tempfile
import subprocess
import uuid
from pathlib import Path
from typing import Union

import docker


class Runtime:
    """Cada instância corresponde a um diretório + container dedicados."""

    def __init__(self, image: str | None = None) -> None:
        self.base_dir = Path(tempfile.mkdtemp(prefix="pygent_"))
        self.image = image or os.getenv("PYGENT_IMAGE", "python:3.12-slim")
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

    # ---------------- public API ----------------
    def bash(self, cmd: str, timeout: int = 30) -> str:
        """Roda comando dentro do container e devolve saída combinada."""
        res = self.container.exec_run(cmd, workdir="/workspace", demux=True, tty=False, timeout=timeout)
        stdout, stderr = res.output if isinstance(res.output, tuple) else (res.output, b"")
        return (stdout or b"").decode() + (stderr or b"").decode()

    def write_file(self, rel_path: Union[str, Path], content: str) -> str:
        p = self.base_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Wrote {p.relative_to(self.base_dir)}"

    def cleanup(self) -> None:
        try:
            self.container.kill()
        finally:
            self.container.remove(force=True)
            shutil.rmtree(self.base_dir, ignore_errors=True)
