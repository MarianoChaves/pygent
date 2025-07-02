"""Pygent package."""
from importlib import metadata as _metadata
from pathlib import Path

from .config import load_config

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

from .agent import Agent, run_interactive  # noqa: E402,F401, must come after __version__
from .models import Model, OpenAIModel, set_custom_model  # noqa: E402,F401
from .errors import PygentError, APIError  # noqa: E402,F401
from .tools import register_tool, tool, clear_tools, reset_tools, remove_tool  # noqa: E402,F401
from .task_manager import TaskManager  # noqa: E402,F401

__all__ = [
    "Agent",
    "run_interactive",
    "load_config",
    "Model",
    "OpenAIModel",
    "set_custom_model",
    "PygentError",
    "APIError",
    "register_tool",
    "tool",
    "clear_tools",
    "reset_tools",
    "remove_tool",
    "TaskManager",
]
