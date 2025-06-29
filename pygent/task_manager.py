from __future__ import annotations

"""Manage background tasks executed by sub-agents."""

import os
import shutil
import threading
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, TYPE_CHECKING

from .runtime import Runtime

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from .agent import Agent


@dataclass
class Task:
    """Represents a delegated task."""

    id: str
    agent: "Agent"
    thread: threading.Thread
    status: str = field(default="running")


class TaskManager:
    """Launch agents asynchronously and track their progress."""

    def __init__(
        self,
        agent_factory: Callable[[], "Agent"] | None = None,
        max_tasks: int | None = None,
    ) -> None:
        from .agent import Agent  # local import to avoid circular dependency

        env_max = os.getenv("PYGENT_MAX_TASKS")
        self.max_tasks = max_tasks if max_tasks is not None else int(env_max or "3")
        self.agent_factory = agent_factory or Agent
        self.tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    def start_task(
        self,
        prompt: str,
        parent_rt: Runtime,
        files: list[str] | None = None,
        parent_depth: int = 0,
    ) -> str:
        """Create a new agent and run ``prompt`` asynchronously."""

        if parent_depth >= 1:
            raise RuntimeError("nested delegation is not allowed")

        with self._lock:
            active = sum(t.status == "running" for t in self.tasks.values())
            if active >= self.max_tasks:
                raise RuntimeError(f"max {self.max_tasks} tasks reached")

        agent = self.agent_factory()
        setattr(agent.runtime, "task_depth", parent_depth + 1)
        if files:
            for fp in files:
                src = parent_rt.base_dir / fp
                dest = agent.runtime.base_dir / fp
                if src.is_dir():
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                elif src.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src, dest)
        task_id = uuid.uuid4().hex[:8]
        task = Task(id=task_id, agent=agent, thread=None)  # type: ignore[arg-type]

        def run() -> None:
            try:
                agent.run_until_stop(prompt)
                task.status = "finished"
            except Exception as exc:  # pragma: no cover - error propagation
                task.status = f"error: {exc}"

        t = threading.Thread(target=run, daemon=True)
        task.thread = t
        with self._lock:
            self.tasks[task_id] = task
        t.start()
        return task_id

    def status(self, task_id: str) -> str:
        with self._lock:
            task = self.tasks.get(task_id)
        if not task:
            return f"Task {task_id} not found"
        return task.status

    def collect_file(self, rt: Runtime, task_id: str, path: str) -> str:
        """Copy a file from a task workspace into ``rt``."""

        with self._lock:
            task = self.tasks.get(task_id)
        if not task:
            return f"Task {task_id} not found"
        src = task.agent.runtime.base_dir / path
        if not src.exists():
            return f"file {path} not found"
        dest = rt.base_dir / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        return f"Retrieved {dest.relative_to(rt.base_dir)}"
