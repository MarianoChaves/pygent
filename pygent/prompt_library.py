"""Collection of ready-made system message builders for different agent styles."""
from __future__ import annotations

from typing import Optional, List, Callable

from .persona import Persona
from . import system_message as agent


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
    lines = []
    for line in base.splitlines():
        if line.startswith("User:"):
            continue
        lines.append(line.replace("the user's request", "the given task"))
    base = "\n".join(lines)
    return (
        base
        + "\nOperate autonomously. Your next exchange will be with yourself, "
        + "no further user messages will arrive."
        + " You have a computing environment at your disposal; begin by "
        + "inspecting it and the available tools."
        + " Execute the initial task step by step using professional,"
        + " state-of-the-art methods unless simplicity is preferable."
        + " Test your work and produce a final artefact or concise summary "
        + "before invoking the `stop` tool, describing the outcome and any "
        + "remaining issues. Continue iterating until satisfied."
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
