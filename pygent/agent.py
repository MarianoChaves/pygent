"""Orchestration layer: receives messages, calls the OpenAI-compatible backend and dispatches tools."""

import json
import os
import pathlib
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .runtime import Runtime
from . import tools
from .models import Model, OpenAIModel

DEFAULT_MODEL = os.getenv("PYGENT_MODEL", "gpt-4.1-mini")
SYSTEM_MSG = (
    "You are Pygent, a sandboxed coding assistant.\n"
    "Respond with JSON when you need to use a tool."
    "If you need to stop or finished you task, call the `stop` tool.\n"
    "You can use the following tools:\n"
    f"{json.dumps(tools.TOOL_SCHEMAS, indent=2)}\n"
    "You can also use the `continue` tool to request user input or continue the conversation.\n"
)

console = Console()




@dataclass
class Agent:
    runtime: Runtime = field(default_factory=Runtime)
    model: Model = field(default_factory=OpenAIModel)
    model_name: str = DEFAULT_MODEL
    system_msg: str = SYSTEM_MSG
    history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.history:
            self.history.append({"role": "system", "content": self.system_msg})

    def step(self, user_msg: str):
        self.history.append({"role": "user", "content": user_msg})
        assistant_msg = self.model.chat(
            self.history, self.model_name, tools.TOOL_SCHEMAS
        )
        self.history.append(assistant_msg)

        if assistant_msg.tool_calls:
            for call in assistant_msg.tool_calls:
                output = tools.execute_tool(call, self.runtime)
                self.history.append({"role": "tool", "content": output, "tool_call_id": call.id})
                console.print(Panel(output, title=f"tool:{call.function.name}"))
        else:
            markdown_response = Markdown(assistant_msg.content)
            console.print(Panel(markdown_response, title="Resposta do Agente", title_align="left", border_style="cyan"))
        return assistant_msg

    def run_until_stop(self, user_msg: str, max_steps: int = 10) -> None:
        """Run steps automatically until the model calls the ``stop`` tool or
        the step limit is reached."""
        msg = user_msg
        for _ in range(max_steps):
            assistant_msg = self.step(msg)
            calls = assistant_msg.tool_calls or []
            if any(c.function.name in ("stop", "continue") for c in calls):
                break
            msg = "continue"


def run_interactive(use_docker: bool | None = None) -> None:  # pragma: no cover
    agent = Agent(runtime=Runtime(use_docker=use_docker))
    console.print("[bold green]Pygent[/] iniciado. (digite /exit para sair)")
    try:
        while True:
            user_msg = console.input("[cyan]user> [/]" )
            if user_msg.strip() in {"/exit", "quit", "q"}:
                break
            agent.run_until_stop(user_msg)
    finally:
        agent.runtime.cleanup()
