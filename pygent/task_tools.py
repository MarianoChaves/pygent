from __future__ import annotations

"""Optional tools for background tasks and personas."""

import json
from typing import Optional

from .runtime import Runtime
from .task_manager import TaskManager
from .tools import register_tool

_task_manager: Optional[TaskManager] = None


def _get_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def get_task_manager() -> TaskManager:
    """Return the lazily-created manager used by task tools."""
    return _get_manager()


def set_task_manager(manager: TaskManager) -> None:
    """Override the manager instance (used by tests and integration layers)."""
    global _task_manager
    _task_manager = manager


# ---- tool implementations ----
from .tools import _download_file


def _delegate_task(
    rt: Runtime,
    prompt: str,
    files: Optional[list[str]] = None,
    timeout: Optional[float] = None,
    step_timeout: Optional[float] = None,
    persona: Optional[str] = None,
) -> str:
    if getattr(rt, "task_depth", 0) >= 1:
        return "error: delegation not allowed in sub-tasks"
    try:
        tid = _get_manager().start_task(
            prompt,
            parent_rt=rt,
            files=files,
            parent_depth=getattr(rt, "task_depth", 0),
            step_timeout=step_timeout,
            task_timeout=timeout,
            persona=persona,
        )
    except RuntimeError as exc:
        return str(exc)
    return f"started {tid}"


def _delegate_persona_task(
    rt: Runtime,
    prompt: str,
    persona: str,
    files: Optional[list[str]] = None,
    timeout: Optional[float] = None,
    step_timeout: Optional[float] = None,
) -> str:
    return _delegate_task(
        rt,
        prompt=prompt,
        files=files,
        timeout=timeout,
        step_timeout=step_timeout,
        persona=persona,
    )


def _list_personas(rt: Runtime) -> str:
    personas = [
        {"name": p.name, "description": p.description}
        for p in _get_manager().personas
    ]
    return json.dumps(personas)


def _task_status(rt: Runtime, task_id: str) -> str:
    return _get_manager().status(task_id)


def _collect_file(rt: Runtime, task_id: str, path: str, dest: Optional[str] = None) -> str:
    return _get_manager().collect_file(rt, task_id, path, dest)


def register_task_tools() -> None:
    """Register task-related tools."""
    register_tool(
        "delegate_task",
        "Create a background task using a new agent and return its ID.",
        {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Instruction for the sub-agent"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files to copy to the sub-agent before starting",
                },
                "persona": {"type": "string", "description": "Persona for the sub-agent"},
                "timeout": {"type": "number", "description": "Max seconds for the task"},
                "step_timeout": {"type": "number", "description": "Time limit per step"},
            },
            "required": ["prompt"],
        },
        lambda rt, **kwargs: _delegate_task(rt, **kwargs),
    )

    register_tool(
        "delegate_persona_task",
        "Create a background task with a specific persona and return its ID.",
        {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Instruction for the sub-agent"},
                "persona": {"type": "string", "description": "Persona for the sub-agent"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files to copy to the sub-agent before starting",
                },
                "timeout": {"type": "number", "description": "Max seconds for the task"},
                "step_timeout": {"type": "number", "description": "Time limit per step"},
            },
            "required": ["prompt", "persona"],
        },
        lambda rt, **kwargs: _delegate_persona_task(rt, **kwargs),
    )

    register_tool(
        "list_personas",
        "Return the available personas for delegated agents.",
        {"type": "object", "properties": {}},
        lambda rt, **kwargs: _list_personas(rt, **kwargs),
    )

    register_tool(
        "task_status",
        "Check the status of a delegated task.",
        {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
        lambda rt, **kwargs: _task_status(rt, **kwargs),
    )

    register_tool(
        "collect_file",
        "Retrieve a file or directory from a delegated task.",
        {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "path": {"type": "string"},
                "dest": {"type": "string"},
            },
            "required": ["task_id", "path"],
        },
        lambda rt, **kwargs: _collect_file(rt, **kwargs),
    )

    register_tool(
        "download_file",
        "Return the contents of a file from the workspace.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "binary": {"type": "boolean"},
            },
            "required": ["path"],
        },
        lambda rt, **kwargs: _download_file(rt, **kwargs),
    )
