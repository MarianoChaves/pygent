"""Tool registry and helper utilities."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional
from copy import deepcopy

from .runtime import Runtime
from .task_manager import TaskManager

_task_manager: Optional[TaskManager] = None


def _get_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


# ---- registry ----
TOOLS: Dict[str, Callable[..., str]] = {}
TOOL_SCHEMAS: List[Dict[str, Any]] = []


def register_tool(
    name: str, description: str, parameters: Dict[str, Any], func: Callable[..., str]
) -> None:
    """Register a new callable tool."""
    if name in TOOLS:
        raise ValueError(f"tool {name} already registered")
    TOOLS[name] = func
    TOOL_SCHEMAS.append(
        {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
    )


def tool(name: str, description: str, parameters: Dict[str, Any]):
    """Decorator for registering a tool."""

    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        register_tool(name, description, parameters, func)
        return func

    return decorator


def execute_tool(call: Any, rt: Runtime) -> str:  # pragma: no cover
    """Dispatch a tool call."""
    name = call.function.name
    args: Dict[str, Any] = json.loads(call.function.arguments)
    func = TOOLS.get(name)
    if func is None:
        return f"⚠️ unknown tool {name}"
    return func(rt, **args)


# ---- built-ins ----


@tool(
    name="bash",
    description="Run a shell command inside the sandboxed container.",
    parameters={
        "type": "object",
        "properties": {"cmd": {"type": "string", "description": "Command to execute"}},
        "required": ["cmd"],
    },
)
def _bash(rt: Runtime, cmd: str) -> str:
    return rt.bash(cmd)


@tool(
    name="write_file",
    description="Create or overwrite a file in the workspace.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"],
    },
)
def _write_file(rt: Runtime, path: str, content: str) -> str:
    return rt.write_file(path, content)


def _upload_file(rt: Runtime, src: str, dest: Optional[str] = None) -> str:
    """Copy a local file or directory into the workspace."""
    return rt.upload_file(src, dest)


@tool(
    name="stop",
    description="Stop the autonomous loop. This is a side-effect free tool that does not return any output. Use when finished some task or when you want to stop the agent.",
    parameters={"type": "object", "properties": {}},
)
def _stop(rt: Runtime) -> str:  # pragma: no cover - side-effect free
    return "Stopping."


@tool(
    name="continue",
    description="Request user answer or input. If in your previous message you asked for user input, you can use this tool to continue the conversation.",
    parameters={"type": "object", "properties": {}},
)
def _continue(rt: Runtime) -> str:  # pragma: no cover - side-effect free
    return "Continuing the conversation."




@tool(
    name="delegate_task",
    description="Create a background task using a new agent and return its ID.",
    parameters={
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
)
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


@tool(
    name="delegate_persona_task",
    description="Create a background task with a specific persona and return its ID.",
    parameters={
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
)
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


@tool(
    name="list_personas",
    description="Return the available personas for delegated agents.",
    parameters={"type": "object", "properties": {}},
)
def _list_personas(rt: Runtime) -> str:
    """Return JSON list of personas."""
    personas = [
        {"name": p.name, "description": p.description}
        for p in _get_manager().personas
    ]
    return json.dumps(personas)


@tool(
    name="task_status",
    description="Check the status of a delegated task.",
    parameters={
        "type": "object",
        "properties": {"task_id": {"type": "string"}},
        "required": ["task_id"],
    },
)
def _task_status(rt: Runtime, task_id: str) -> str:
    return _get_manager().status(task_id)


def _collect_file(rt: Runtime, task_id: str, path: str, dest: Optional[str] = None) -> str:
    """Retrieve a file or directory from a delegated task."""
    return _get_manager().collect_file(rt, task_id, path, dest)


def _download_file(rt: Runtime, path: str, binary: bool = False) -> str:
    """Return the contents of a file from the workspace."""
    return rt.read_file(path, binary=binary)

# snapshot of the default built-in registry
BUILTIN_TOOLS = TOOLS.copy()
BUILTIN_TOOL_SCHEMAS = deepcopy(TOOL_SCHEMAS)


def clear_tools() -> None:
    """Remove all registered tools globally."""
    TOOLS.clear()
    TOOL_SCHEMAS.clear()


def reset_tools() -> None:
    """Restore the default built-in tools."""
    clear_tools()
    TOOLS.update(BUILTIN_TOOLS)
    TOOL_SCHEMAS.extend(deepcopy(BUILTIN_TOOL_SCHEMAS))


def remove_tool(name: str) -> None:
    """Unregister a specific tool."""
    if name not in TOOLS:
        raise ValueError(f"tool {name} not registered")
    del TOOLS[name]
    for i, schema in enumerate(TOOL_SCHEMAS):
        func = schema.get("function", {})
        if func.get("name") == name:
            TOOL_SCHEMAS.pop(i)
            break

