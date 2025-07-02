from __future__ import annotations

"""Optional tools for background tasks and personas."""

import json
from typing import Optional, List

from .runtime import Runtime
from .task_manager import TaskManager
from .tools import register_tool

_task_manager: Optional[TaskManager] = None


def _get_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


# ---- tool implementations ----
from .tools import (
    _delegate_task,
    _delegate_persona_task,
    _list_personas,
    _task_status,
    _collect_file,
    _download_file,
)


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
