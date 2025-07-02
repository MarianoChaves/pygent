"""Orchestration layer: receives messages, calls the OpenAI-compatible backend and dispatches tools."""

import json
import os
import pathlib
import uuid
import time
from dataclasses import dataclass, field, asdict
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


def _default_history_file() -> Optional[pathlib.Path]:
    env = os.getenv("PYGENT_HISTORY_FILE")
    return pathlib.Path(env) if env else None


@dataclass
class Agent:
    """Interactive assistant handling messages and tool execution."""
    runtime: Runtime = field(default_factory=Runtime)
    model: Model = field(default_factory=_default_model)
    model_name: str = DEFAULT_MODEL
    persona: Persona = field(default_factory=lambda: DEFAULT_PERSONA)
    system_msg: str = field(default_factory=lambda: build_system_msg(DEFAULT_PERSONA))
    history: List[Dict[str, Any]] = field(default_factory=list)
    history_file: Optional[pathlib.Path] = field(default_factory=_default_history_file)

    def __post_init__(self) -> None:
        """Initialize defaults after dataclass construction."""
        if not self.system_msg:
            self.system_msg = build_system_msg(self.persona)
        if self.history_file and isinstance(self.history_file, (str, pathlib.Path)):
            self.history_file = pathlib.Path(self.history_file)
            if self.history_file.is_file():
                try:
                    with self.history_file.open("r", encoding="utf-8") as fh:
                        data = json.load(fh)
                except Exception:
                    data = []
                self.history = [
                    openai_compat.parse_message(m) if isinstance(m, dict) else m
                    for m in data
                ]
        if not self.history:
            self.append_history({"role": "system", "content": self.system_msg})

    def _message_dict(self, msg: Any) -> Dict[str, Any]:
        if isinstance(msg, dict):
            return msg
        if isinstance(msg, openai_compat.Message):
            data = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                data["tool_calls"] = [asdict(tc) for tc in msg.tool_calls]
            return data
        raise TypeError(f"Unsupported message type: {type(msg)!r}")

    def _save_history(self) -> None:
        if self.history_file:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with self.history_file.open("w", encoding="utf-8") as fh:
                json.dump([self._message_dict(m) for m in self.history], fh)

    def append_history(self, msg: Any) -> None:
        self.history.append(msg)
        self._save_history()

    def refresh_system_message(self) -> None:
        """Update the system prompt based on the current tool registry."""
        self.system_msg = build_system_msg(self.persona)
        if self.history and self.history[0].get("role") == "system":
            self.history[0]["content"] = self.system_msg

    def step(self, user_msg: str):
        """Execute one round of interaction with the model."""

        self.refresh_system_message()
        self.append_history({"role": "user", "content": user_msg})

        assistant_raw = self.model.chat(
            self.history, self.model_name, tools.TOOL_SCHEMAS
        )
        assistant_msg = openai_compat.parse_message(assistant_raw)
        self.append_history(assistant_msg)

        if assistant_msg.tool_calls:
            for call in assistant_msg.tool_calls:
                output = tools.execute_tool(call, self.runtime)
                self.append_history(
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
                self.append_history(
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
                self.append_history(
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
    agent = Agent(runtime=Runtime(use_docker=use_docker))
    mode = "Docker" if agent.runtime.use_docker else "local"
    console.print(
        f"[bold green]{agent.persona.name} ({mode})[/] iniciado. (digite /exit para sair)"
    )
    try:
        while True:
            user_msg = console.input("[cyan]user> [/]")
            if user_msg.strip() in {"/exit", "quit", "q"}:
                break
            agent.run_until_stop(user_msg)
    finally:
        agent.runtime.cleanup()
