"""Orchestration layer: receives messages, calls the OpenAI-compatible backend and dispatches tools."""

import json
import os
import pathlib
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .runtime import Runtime
from . import tools, models, openai_compat
from .models import Model, OpenAIModel
from .persona import Persona

DEFAULT_PERSONA = Persona(
    os.getenv("PYGENT_PERSONA_NAME", "Pygent"),
    os.getenv("PYGENT_PERSONA", "a sandboxed coding assistant."),
)


def build_system_msg(persona: Persona) -> str:
    """Return the system prompt for ``persona``."""

    return (
        f"You are {persona.name}. {persona.description}\n"
        "Respond with JSON when you need to use a tool."
        "If you need to stop or finish your task, call the `stop` tool.\n"
        "You can use the following tools:\n"
        f"{json.dumps(tools.TOOL_SCHEMAS, indent=2)}\n"
        "You can also use the `continue` tool to request user input or continue the conversation.\n"
    )


DEFAULT_MODEL = os.getenv("PYGENT_MODEL", "gpt-4.1-mini")
SYSTEM_MSG = build_system_msg(DEFAULT_PERSONA)

console = Console()


def _default_model() -> Model:
    """Return the global custom model or the default OpenAI model."""
    return models.CUSTOM_MODEL or OpenAIModel()


@dataclass
class Agent:
    """Interactive assistant handling messages and tool execution."""
    runtime: Runtime = field(default_factory=Runtime)
    model: Model = field(default_factory=_default_model)
    model_name: str = DEFAULT_MODEL
    persona: Persona = field(default_factory=lambda: DEFAULT_PERSONA)
    system_msg: str = field(default_factory=lambda: build_system_msg(DEFAULT_PERSONA))
    history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize defaults after dataclass construction."""
        if not self.system_msg:
            self.system_msg = build_system_msg(self.persona)
        if not self.history:
            self.history.append({"role": "system", "content": self.system_msg})

    def refresh_system_message(self) -> None:
        """Update the system prompt based on the current tool registry."""
        self.system_msg = build_system_msg(self.persona)
        if self.history and self.history[0].get("role") == "system":
            self.history[0]["content"] = self.system_msg

    def step(self, user_msg: str):
        """Execute one round of interaction with the model."""

        self.refresh_system_message()
        self.history.append({"role": "user", "content": user_msg})

        assistant_raw = self.model.chat(
            self.history, self.model_name, tools.TOOL_SCHEMAS
        )
        assistant_msg = openai_compat.parse_message(assistant_raw)
        self.history.append(assistant_msg)

        if assistant_msg.tool_calls:
            for call in assistant_msg.tool_calls:
                output = tools.execute_tool(call, self.runtime)
                self.history.append(
                    {"role": "tool", "content": output, "tool_call_id": call.id}
                )
                console.print(
                    Panel(
                        output,
                        title=f"{self.persona.name} tool:{call.function.name}",
                    )
                )
        else:
            markdown_response = Markdown(assistant_msg.content)
            console.print(
                Panel(
                    markdown_response,
                    title=f"Resposta de {self.persona.name}",
                    title_align="left",
                    border_style="cyan",
                )
            )
        return assistant_msg

    def run_until_stop(
        self,
        user_msg: str,
        max_steps: int = 20,
        step_timeout: Optional[float] = None,
        max_time: Optional[float] = None,
    ) -> None:
        """Run steps until ``stop`` is called or limits are reached."""

        if step_timeout is None:
            env = os.getenv("PYGENT_STEP_TIMEOUT")
            step_timeout = float(env) if env else None
        if max_time is None:
            env = os.getenv("PYGENT_TASK_TIMEOUT")
            max_time = float(env) if env else None

        msg = user_msg
        start = time.monotonic()
        self._timed_out = False
        for _ in range(max_steps):
            if max_time is not None and time.monotonic() - start > max_time:
                self.history.append(
                    {"role": "system", "content": f"[timeout after {max_time}s]"}
                )
                self._timed_out = True
                break
            step_start = time.monotonic()
            assistant_msg = self.step(msg)
            if (
                step_timeout is not None
                and time.monotonic() - step_start > step_timeout
            ):
                self.history.append(
                    {"role": "system", "content": f"[timeout after {step_timeout}s]"}
                )
                self._timed_out = True
                break
            calls = assistant_msg.tool_calls or []
            if any(c.function.name in ("stop", "continue") for c in calls):
                break
            msg = "continue"


def run_interactive(use_docker: Optional[bool] = None) -> None:  # pragma: no cover
    """Start an interactive session in the terminal."""
    main_agent = Agent(runtime=Runtime(use_docker=use_docker))
    manager = tools._get_manager()
    agents: Dict[str, Agent] = {"main": main_agent}
    current = "main"

    mode = "Docker" if main_agent.runtime.use_docker else "local"
    console.print(
        f"[bold green]{main_agent.persona.name} ({mode})[/] iniciado. (digite /exit para sair)"
    )
    try:
        while True:
            prompt = console.input(f"[cyan]{current}> [/]" )
            cmd = prompt.strip()
            if cmd in {"/exit", "quit", "q"}:
                break
            if cmd.startswith("/tasks"):
                tasks = manager.list_tasks()
                active = sum(1 for info in tasks.values() if info["status"] == "running")
                active += 1  # main agent
                console.print(f"Agentes ativos: {active}")
                for tid, info in tasks.items():
                    console.print(f"{tid}: {info['persona']} - {info['status']}")
                continue
            if cmd.startswith("/switch"):
                parts = cmd.split(maxsplit=1)
                if len(parts) == 2:
                    tid = parts[1]
                    if tid == "main":
                        current = "main"
                        console.print("troquei para agente principal")
                    else:
                        ag = manager.get_agent(tid)
                        if ag:
                            agents[tid] = ag
                            current = tid
                            console.print(f"troquei para {tid}")
                        else:
                            console.print(f"Task {tid} não encontrada")
                else:
                    console.print("uso: /switch TASK_ID")
                continue
            if cmd.startswith("/talk"):
                parts = cmd.split(maxsplit=2)
                if len(parts) >= 3:
                    tid = parts[1]
                    msg = parts[2]
                    ag = manager.get_agent(tid)
                    if ag:
                        ag.run_until_stop(msg)
                    else:
                        console.print(f"Task {tid} não encontrada")
                else:
                    console.print("uso: /talk TASK_ID MENSAGEM")
                continue
            agents[current].run_until_stop(prompt)
    finally:
        seen = {ag.runtime for ag in agents.values()}
        for t in manager.tasks.values():
            seen.add(t.agent.runtime)
        for rt in seen:
            try:
                rt.cleanup()
            except Exception:
                pass
