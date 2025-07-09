"""Pygent package."""
from importlib import metadata as _metadata
from pathlib import Path

from .config import load_config, load_snapshot

try:
    __version__: str = _metadata.version(__name__)
except _metadata.PackageNotFoundError:  # pragma: no cover - fallback for tests
    try:  # Python 3.11+
        import tomllib  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - executed on older Python versions
        import tomli as tomllib  # type: ignore

    _root = Path(__file__).resolve().parent.parent
    pyproject = _root / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as fh:
            data = tomllib.load(fh)
        __version__ = data.get("project", {}).get("version", "0.0.0")
    else:
        __version__ = "0.0.0"

from .agent import (
    Agent,
    run_interactive,
    set_system_message_builder,
)
from .models import Model, OpenAIModel, set_custom_model  # noqa: E402,F401
from .errors import PygentError, APIError  # noqa: E402,F401
from .tools import register_tool, tool, clear_tools, reset_tools, remove_tool  # noqa: E402,F401
from .task_manager import TaskManager  # noqa: E402,F401
from .task_tools import register_task_tools  # noqa: E402,F401
from .prompt_library import PROMPT_BUILDERS  # noqa: E402,F401
from .agent_presets import AGENT_PRESETS, AgentPreset  # noqa: E402,F401

__all__ = [
    "Agent",
    "run_interactive",
    "load_config",
    "load_snapshot",
    "Model",
    "OpenAIModel",
    "set_custom_model",
    "set_system_message_builder",
    "PygentError",
    "APIError",
    "register_tool",
    "tool",
    "clear_tools",
    "reset_tools",
    "remove_tool",
    "TaskManager",
    "register_task_tools",
    "PROMPT_BUILDERS",
    "AGENT_PRESETS",
    "AgentPreset",
]
