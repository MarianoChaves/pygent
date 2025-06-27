"""Pygent package."""
from importlib import metadata as _metadata

try:
    __version__: str = _metadata.version(__name__)
except _metadata.PackageNotFoundError:  # pragma: no cover - fallback for tests
    __version__ = "0.0.0"

from .agent import Agent, run_interactive  # noqa: E402,F401, must come after __version__

__all__ = ["Agent", "run_interactive"]
