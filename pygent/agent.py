"""Orchestration layer: receives messages, calls the OpenAI-compatible backend and dispatches tools."""

import json
import os
import pathlib
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

try:
    import openai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback to bundled client
    from . import openai_compat as openai
from rich.console import Console
from rich.panel import Panel

from .runtime import Runtime
from .tools import TOOL_SCHEMAS, execute_tool

MODEL = os.getenv("PYGENT_MODEL", "gpt-4o-mini-preview")
SYSTEM_MSG = (
    "You are Pygent, a sandboxed coding assistant.\n"
    "Respond with JSON when you need to use a tool."
)

console = Console()


def _chat(messages: List[Dict[str, str]]) -> str:
    resp = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
    )
    return resp.choices[0].message


@dataclass
class Agent:
    runtime: Runtime = field(default_factory=Runtime)
    history: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"role": "system", "content": SYSTEM_MSG}
    ])

    def step(self, user_msg: str) -> None:
        self.history.append({"role": "user", "content": user_msg})
        assistant_msg = _chat(self.history)
        self.history.append(assistant_msg)

        if assistant_msg.tool_calls:
            for call in assistant_msg.tool_calls:
                output = execute_tool(call, self.runtime)
                self.history.append({"role": "tool", "content": output, "tool_call_id": call.id})
                console.print(Panel(output, title=f"tool:{call.function.name}"))
        else:
            console.print(assistant_msg.content)


def run_interactive(use_docker: bool | None = None) -> None:  # pragma: no cover
    agent = Agent(runtime=Runtime(use_docker=use_docker))
    console.print("[bold green]Pygent[/] iniciado. (digite /exit para sair)")
    try:
        while True:
            user_msg = console.input("[cyan]vc> [/]" )
            if user_msg.strip() in {"/exit", "quit", "q"}:
                break
            agent.step(user_msg)
    finally:
        agent.runtime.cleanup()
