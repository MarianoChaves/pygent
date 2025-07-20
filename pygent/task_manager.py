from __future__ import annotations

"""Manage background tasks executed by sub-agents."""

import os
import json
import shutil
import threading
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, TYPE_CHECKING, Optional, Union

from .persona import Persona

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
        agent_factory: Optional[Callable[..., "Agent"]] = None,
        max_tasks: Optional[int] = None,
        personas: Optional[list[Persona]] = None,
    ) -> None:
        from .agent import Agent  # local import to avoid circular dependency

        env_max = os.getenv("PYGENT_MAX_TASKS")
        self.max_tasks = max_tasks if max_tasks is not None else int(env_max or "3")
        if agent_factory is None:
            self.agent_factory = lambda p=None: Agent(persona=p)
        else:
            self.agent_factory = agent_factory
        env_personas_json = os.getenv("PYGENT_TASK_PERSONAS_JSON")
        if personas is None and env_personas_json:
            try:
                data = json.loads(env_personas_json)
                if isinstance(data, list):
                    personas = [
                        Persona(p.get("name", ""), p.get("description", ""))
                        for p in data
                        if isinstance(p, dict)
                    ]
            except Exception:
                personas = None
        env_personas = os.getenv("PYGENT_TASK_PERSONAS")
        if personas is None and env_personas:
            personas = [
                Persona(p.strip(), "")
                for p in env_personas.split(os.pathsep)
                if p.strip()
            ]
        if personas is None:
            personas = [
                Persona(
                    os.getenv("PYGENT_PERSONA_NAME", "Pygent"),
                    os.getenv("PYGENT_PERSONA", "a sandboxed coding assistant."),
                )
            ]
        self.personas = personas
        self._persona_idx = 0
        self.tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    def start_task(
        self,
        prompt: str,
        parent_rt: Runtime,
        files: Optional[list[str]] = None,
        parent_depth: int = 0,
        step_timeout: Optional[float] = None,
        task_timeout: Optional[float] = None,
        persona: Union[Persona, str, None] = None,
    ) -> str:
        """Create a new agent and run ``prompt`` asynchronously.

        ``persona`` overrides the default rotation used for delegated tasks.
        """

        if parent_depth >= 1:
            raise RuntimeError("nested delegation is not allowed")

        with self._lock:
            active = sum(t.status == "running" for t in self.tasks.values())
            if active >= self.max_tasks:
                raise RuntimeError(f"max {self.max_tasks} tasks reached")

        if step_timeout is None:
            env = os.getenv("PYGENT_STEP_TIMEOUT")
            step_timeout = float(env) if env else 60 * 5  # default 5 minutes
        if task_timeout is None:
            env = os.getenv("PYGENT_TASK_TIMEOUT")
            task_timeout = float(env) if env else 60 * 20  # default 20 minutes

        if persona is None:
            persona = self.personas[self._persona_idx % len(self.personas)]
            self._persona_idx += 1
        elif isinstance(persona, str):
            match = next((p for p in self.personas if p.name == persona), None)
            persona = match or Persona(persona, "")
        try:
            agent = self.agent_factory(persona)
        except TypeError:
            agent = self.agent_factory()

        from .runtime import Runtime
        if getattr(agent, "runtime", None) is not None:
            try:
                agent.runtime.cleanup()
            except Exception:
                pass
        task_dir = parent_rt.base_dir / f"task_{uuid.uuid4().hex[:8]}"
        agent.runtime = Runtime(use_docker=parent_rt.use_docker, workspace=task_dir)
        setattr(agent, "persona", persona)
        if not getattr(agent, "system_msg", None):
            from .system_message import build_system_msg  # lazy import

            agent.system_msg = build_system_msg(persona)
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
                agent.run_until_stop(
                    prompt,
                    step_timeout=step_timeout,
                    max_time=task_timeout,
                )
                if getattr(agent, "_timed_out", False):
                    task.status = f"timeout after {task_timeout}s"
                else:
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

    def collect_file(
        self, rt: Runtime, task_id: str, path: str, dest: Optional[str] = None
    ) -> str:
        """Copy a file or directory from a task workspace into ``rt``."""

        with self._lock:
            task = self.tasks.get(task_id)
        if not task:
            return f"Task {task_id} not found"
        src = task.agent.runtime.base_dir / path
        if not src.exists():
            return f"file {path} not found"
        dest_path = rt.base_dir / (dest or path)
        if src.is_dir():
            shutil.copytree(src, dest_path, dirs_exist_ok=True)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dest_path)
        return f"Retrieved {dest_path.relative_to(rt.base_dir)}"
