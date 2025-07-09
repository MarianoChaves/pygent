"""Collection of ready-made system message builders for different agent styles."""
from __future__ import annotations

from typing import Optional, List, Callable

from .persona import Persona
from . import agent


def _base_system_msg(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Return the default system message ignoring any custom builder."""
    current = agent._SYSTEM_MSG_BUILDER
    agent._SYSTEM_MSG_BUILDER = None
    try:
        return agent.build_system_msg(persona, disabled_tools)
    finally:
        agent._SYSTEM_MSG_BUILDER = current


def autonomous_builder(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Prompt emphasising fully autonomous operation."""
    base = _base_system_msg(persona, disabled_tools)
    return (
        base
        + "\nYou are not an assistant and will not receive user input."
        + " Act autonomously to solve the task without redirecting questions."
        + " Provide a complete, professional solution using state-of-the-art"
        + " methods unless a simpler approach is requested."
        + " Test your work before calling the `stop` tool and summarise what"
        + " you accomplished along with any remaining issues."
        + " Continue iterating until satisfied."
    )


def assistant_builder(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Prompt tuned for interactive assistant behaviour."""
    base = _base_system_msg(persona, disabled_tools)
    return base + "\nEngage the user actively, asking for clarification whenever it might help."


def reviewer_builder(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Prompt that focuses on reviewing and improving code."""
    base = _base_system_msg(persona, disabled_tools)
    return base + "\nFocus on analysing existing code, pointing out bugs and suggesting improvements."


PROMPT_BUILDERS: dict[str, Callable[[Persona, Optional[List[str]]], str]] = {
    "autonomous": autonomous_builder,
    "assistant": assistant_builder,
    "reviewer": reviewer_builder,
}
