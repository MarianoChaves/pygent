"""Predefined agent presets combining prompt builders and tool sets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from .persona import Persona
from .agent import Agent, set_system_message_builder
from .tools import reset_tools, remove_tool, TOOLS
from .prompt_library import PROMPT_BUILDERS
from .task_tools import register_task_tools


@dataclass
class AgentPreset:
    """Factory for an :class:`~pygent.agent.Agent` with preset behaviour."""

    builder: Callable[[Persona, Optional[List[str]]], str]
    tools: Optional[List[str]] = None
    include_task_tools: bool = False

    def create_agent(self, **kwargs) -> Agent:
        """Return an :class:`~pygent.agent.Agent` using this preset."""

        # Build the agent first with the default system message to avoid
        # recursive calls when the custom builder relies on ``build_system_msg``.
        set_system_message_builder(None)
        reset_tools()
        if self.include_task_tools:
            register_task_tools()
        if self.tools is not None:
            allowed = set(self.tools)
            for name in list(TOOLS):
                if name not in allowed:
                    remove_tool(name)
        agent = Agent(**kwargs)
        # Now enable the custom builder and refresh the system message so the
        # first history entry reflects it.
        set_system_message_builder(self.builder)
        agent.refresh_system_message()
        return agent


AGENT_PRESETS: dict[str, AgentPreset] = {
    "autonomous": AgentPreset(
        PROMPT_BUILDERS["autonomous"],
        tools=["bash", "write_file", "stop", "read_image"],
        include_task_tools=False,
    ),
    "assistant": AgentPreset(
        PROMPT_BUILDERS["assistant"],
        tools=["bash", "write_file", "ask_user", "stop", "read_image"],
        include_task_tools=False,
    ),
    "reviewer": AgentPreset(
        PROMPT_BUILDERS["reviewer"],
        tools=["bash", "stop", "read_image"],
        include_task_tools=False,
    ),
}
