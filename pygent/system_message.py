"""System message builder and default persona for Pygent."""
from __future__ import annotations

import json
import os
import platform
import shutil
from typing import Callable, List, Optional

from .persona import Persona
from . import tools

# optional custom builder for the system message
_SYSTEM_MSG_BUILDER: Optional[Callable[[Persona, Optional[List[str]]], str]] = None


def set_system_message_builder(
    builder: Optional[Callable[[Persona, Optional[List[str]]], str]]
) -> None:
    """Register a callable to build the system prompt."""

    global _SYSTEM_MSG_BUILDER
    _SYSTEM_MSG_BUILDER = builder


DEFAULT_PERSONA = Persona(
    os.getenv("PYGENT_PERSONA_NAME", "Pygent"),
    os.getenv("PYGENT_PERSONA", "a sandboxed coding assistant."),
)


def build_system_msg(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Build the system prompt for ``persona`` with the active tools."""

    if _SYSTEM_MSG_BUILDER:
        return _SYSTEM_MSG_BUILDER(persona, disabled_tools)

    # Active tool schemas
    schemas = [
        s for s in tools.TOOL_SCHEMAS
        if not disabled_tools or s["function"]["name"] not in disabled_tools
    ]
    has_bash = any(s["function"]["name"] == "bash" for s in schemas)

    # 1) Dynamic prefix
    try:
        user = os.getlogin()
    except Exception:
        user = os.getenv("USER", "unknown")
    dynamic_lines = [
        f"User: {user}",
        f"OS: {platform.system()}",
        f"Working directory: {os.getcwd()}",
    ]
    if shutil.which("rg"):
        dynamic_lines.append(
            "Hint: prefer `rg` over `grep`/`ls -R`; it is faster and honours .gitignore."
        )
    dynamic_prefix = "\n".join(dynamic_lines)

    # 2) Fixed operation block
    fixed_block = (
        "You are operating as and within a terminal-based coding assistant. "
        "Your task is to satisfy the user's request with precision and safety. "
        "When context is missing, rely on the available tools to inspect files or execute commands. "
    )

    # 3) Workflow block
    has_ask = any(s["function"]["name"] == "ask_user" for s in schemas)
    has_stop = any(s["function"]["name"] == "stop" for s in schemas)
    has_image = any(s["function"]["name"] == "read_image" for s in schemas)

    first_line = "First, present a concise plan (≤ 5 lines)"
    if has_ask:
        first_line += (
            " and end by asking the user permission to procceed, ideally as a short menu."
        )
    else:
        first_line += "."

    second_line = (
        "After approval, move step by step, briefly stating which tool you invoke and why."
        if has_ask
        else "Then move step by step, briefly stating which tool you invoke and why."
    )

    workflow_parts = [first_line, second_line]
    if has_ask:
        workflow_parts.append(
            "If you require additional input, use the `ask_user` tool and provide options when possible."
        )
    workflow_parts.append(
        "Before finalizing, verify and test that the request is fully satisfied. "
        "If not, keep iterating until no more improvements can be made."
    )
    if has_stop:
        workflow_parts.append("When the task is fully complete, use the `stop` tool.")
    workflow_block = " ".join(workflow_parts)

    if has_image:
        workflow_block += (
            " If you need to read an image, use the `read_image` tool and provide a path."
        )
    # 4) Optional bash note
    bash_note = (
        "You can execute shell commands in an isolated environment via the `bash` tool, "
        "including installing dependencies." if has_bash else ""
    )

    # 5) Tools block
    tools_block = f"Available tools:\n{json.dumps(schemas, indent=2)}"

    return (
        f"{dynamic_prefix}\n\n"
        f"{fixed_block}\n\n"
        f"You are {persona.name}. {persona.description}\n\n"
        f"{workflow_block}\n"
        f"{bash_note}\n\n"
        f"{tools_block}\n"
    )


SYSTEM_MSG = build_system_msg(DEFAULT_PERSONA)
