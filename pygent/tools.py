"""Tool registry and helper utilities."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from .runtime import Runtime


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


@tool(
    name="stop",
    description="Stop the autonomous loop.",
    parameters={"type": "object", "properties": {}},
)
def _stop(rt: Runtime) -> str:  # pragma: no cover - side-effect free
    return "Stopping."


@tool(
    name="continue",
    description="Continue the conversation.",
    parameters={"type": "object", "properties": {}},
)
def _continue(rt: Runtime) -> str:  # pragma: no cover - side-effect free
    return "Continuing the conversation."

