"""Pacote Pygent."""
from importlib import metadata as _metadata

__version__: str = _metadata.version(__name__)

from .agent import Agent, run_interactive  # noqa: E402,F401, must come after __version__

__all__ = ["Agent", "run_interactive"]
