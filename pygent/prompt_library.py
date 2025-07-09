"""Collection of ready-made system message builders for different agent styles."""
from __future__ import annotations

from typing import Optional, List, Callable

from .persona import Persona
from .agent import build_system_msg


def autonomous_builder(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Prompt emphasising fully autonomous operation."""
    base = build_system_msg(persona, disabled_tools)
    return base + "\nAct autonomously without expecting user input. When the task is complete use the `stop` tool."


def assistant_builder(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Prompt tuned for interactive assistant behaviour."""
    base = build_system_msg(persona, disabled_tools)
    return base + "\nEngage the user actively, asking for clarification whenever it might help."


def reviewer_builder(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Prompt that focuses on reviewing and improving code."""
    base = build_system_msg(persona, disabled_tools)
    return base + "\nFocus on analysing existing code, pointing out bugs and suggesting improvements."


PROMPT_BUILDERS: dict[str, Callable[[Persona, Optional[List[str]]], str]] = {
    "autonomous": autonomous_builder,
    "assistant": assistant_builder,
    "reviewer": reviewer_builder,
}
