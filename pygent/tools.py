"""Tool registry and helper utilities."""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional
import mimetypes
import imghdr
from pathlib import Path
from copy import deepcopy

from .runtime import Runtime


# ---- registry ----
TOOLS: Dict[str, Callable[..., str]] = {}
TOOL_SCHEMAS: List[Dict[str, Any]] = []
_task_manager: Any = None


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
    """Dispatch a tool call.

    Any exception raised by the tool is caught and returned as an error
    string so callers don't crash the CLI.
    """

    name = call.function.name
    try:
        args: Dict[str, Any] = json.loads(call.function.arguments or "{}")
    except Exception as exc:  # pragma: no cover - defensive
        return f"[error] invalid arguments for {name}: {exc}"

    func = TOOLS.get(name)
    if func is None:
        return f"⚠️ unknown tool {name}"

    try:
        return func(rt, **args)
    except Exception as exc:  # pragma: no cover - tool errors
        return f"[error] {exc}"


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
    name="ask_user",
    description=(
        "Request user answer or input. If in your previous message you asked for user"
        " input, you can use this tool to continue the conversation. Optionally"
        " supply a 'prompt' and a list of 'options' to present a menu."
    ),
    parameters={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "question to present when asking for user input",
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "choices the user can select from",
            },
        },
        "required": [],
    },
)
def _ask_user(
    rt: Runtime, prompt: str | None = None, options: Optional[list[str]] = None
) -> str:  # pragma: no cover - side-effect free
    return "Continuing the conversation."

def _download_file(rt: Runtime, path: str, binary: bool = False) -> str:
    """Return the contents of a file from the workspace."""
    return rt.read_file(path, binary=binary)


# Legacy wrappers kept outside the default tool registry so the core package
# stays focused on a single-agent CLI flow.
def _sync_task_manager() -> None:
    from . import task_tools

    if _task_manager is not None:
        task_tools.set_task_manager(_task_manager)
    else:
        globals()["_task_manager"] = task_tools.get_task_manager()


def _delegate_task(*args: Any, **kwargs: Any) -> str:
    from . import task_tools

    _sync_task_manager()
    return task_tools._delegate_task(*args, **kwargs)


def _delegate_persona_task(*args: Any, **kwargs: Any) -> str:
    from . import task_tools

    _sync_task_manager()
    return task_tools._delegate_persona_task(*args, **kwargs)


def _list_personas(*args: Any, **kwargs: Any) -> str:
    from . import task_tools

    _sync_task_manager()
    return task_tools._list_personas(*args, **kwargs)


def _task_status(*args: Any, **kwargs: Any) -> str:
    from . import task_tools

    _sync_task_manager()
    return task_tools._task_status(*args, **kwargs)


def _collect_file(*args: Any, **kwargs: Any) -> str:
    from . import task_tools

    _sync_task_manager()
    return task_tools._collect_file(*args, **kwargs)


@tool(
    name="read_image",
    description="If you use this tool, you will read the image provided.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the image file"}
        },
        "required": ["path"],
    },
)
def _read_image(rt: Runtime, path: str) -> str:
    """Encode ``path`` and return a data URL."""
    data = rt.read_file(path, binary=True)
    if data.startswith("file "):
        return data
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        guessed = imghdr.what(rt.base_dir / path)
        if guessed:
            mime = f"image/{guessed}"
        else:
            ext = Path(path).suffix.lstrip(".") or "png"
            mime = f"image/{ext}"
    return f"data:{mime};base64,{data}"

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
