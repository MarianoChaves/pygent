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
try:
    from rich import box  # type: ignore
except Exception:  # pragma: no cover - tests stub out rich
    box = None
from contextlib import nullcontext
try:  # pragma: no cover - optional dependency
    import questionary  # type: ignore
except Exception:  # pragma: no cover - used in tests without questionary
    questionary = None

from .runtime import Runtime
from . import tools, models, openai_compat
from .models import Model, OpenAIModel
from .persona import Persona

DEFAULT_PERSONA = Persona(
    os.getenv("PYGENT_PERSONA_NAME", "Pygent"),
    os.getenv("PYGENT_PERSONA", "a sandboxed coding assistant."),
)


def build_system_msg(persona: Persona, disabled_tools: Optional[List[str]] = None) -> str:
    """Return the system prompt for ``persona`` with given tools."""

    schemas = [
        s
        for s in tools.TOOL_SCHEMAS
        if not disabled_tools or s["function"]["name"] not in disabled_tools
    ]

    return (
        f"You are {persona.name}. {persona.description}\n"
        "Think step by step and use the available tools to solve the problem. "
        "Call `stop` when your work is done. Use `continue` if you require user input.\n"
        "Available tools:\n"
        f"{json.dumps(schemas, indent=2)}\n"
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
    disabled_tools: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize defaults after dataclass construction."""
        if not self.system_msg:
            self.system_msg = build_system_msg(self.persona, self.disabled_tools)
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
        self.system_msg = build_system_msg(self.persona, self.disabled_tools)
        if self.history and self.history[0].get("role") == "system":
            self.history[0]["content"] = self.system_msg

    def step(self, user_msg: str):
        """Execute one round of interaction with the model."""

        self.refresh_system_message()
        self.append_history({"role": "user", "content": user_msg})

        status_cm = (
            console.status("[bold cyan]Thinking...", spinner="dots")
            if hasattr(console, "status")
            else nullcontext()
        )
        schemas = [
            s
            for s in tools.TOOL_SCHEMAS
            if s["function"]["name"] not in self.disabled_tools
        ]
        with status_cm:
            assistant_raw = self.model.chat(
                self.history, self.model_name, schemas
            )
        assistant_msg = openai_compat.parse_message(assistant_raw)
        self.append_history(assistant_msg)

        if assistant_msg.tool_calls:
            for call in assistant_msg.tool_calls:
                status_cm = (
                    console.status(
                        f"[green]Running {call.function.name}...", spinner="line"
                    )
                    if hasattr(console, "status")
                    else nullcontext()
                )
                with status_cm:
                    output = tools.execute_tool(call, self.runtime)
                self.append_history(
                    {"role": "tool", "content": output, "tool_call_id": call.id}
                )
                if call.function.name not in {"continue", "stop"}:
                    console.print(
                        Panel(
                            output,
                            title=f"{self.persona.name} tool:{call.function.name}",
                            box=box.ROUNDED if box else None,
                        )
                    )
        else:
            markdown_response = Markdown(assistant_msg.content)
            console.print(
                Panel(
                    markdown_response,
                    title=f"{self.persona.name} replied",
                    title_align="left",
                    border_style="cyan",
                    box=box.ROUNDED if box else None,
                )
            )
        return assistant_msg

    def run_until_stop(
        self,
        user_msg: str,
        max_steps: int = 20,
        step_timeout: Optional[float] = None,
        max_time: Optional[float] = None,
    ) -> Optional[openai_compat.Message]:
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
        last_msg = None
        for _ in range(max_steps):
            if max_time is not None and time.monotonic() - start > max_time:
                self.append_history(
                    {"role": "system", "content": f"[timeout after {max_time}s]"}
                )
                self._timed_out = True
                break
            step_start = time.monotonic()
            assistant_msg = self.step(msg)
            last_msg = assistant_msg
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

        return last_msg


def run_interactive(
    use_docker: Optional[bool] = None,
    workspace_name: Optional[str] = None,
    disabled_tools: Optional[List[str]] = None,
) -> None:  # pragma: no cover
    """Start an interactive session in the terminal."""
    ws = pathlib.Path.cwd() / workspace_name if workspace_name else None
    agent = Agent(
        runtime=Runtime(use_docker=use_docker, workspace=ws),
        disabled_tools=disabled_tools or [],
    )
    from .commands import COMMANDS
    mode = "Docker" if agent.runtime.use_docker else "local"
    console.print(
        f"[bold green]{agent.persona.name} ({mode})[/] started. (type /exit to quit)"
    )
    console.print("Type /help for available commands.")
    try:
        next_msg: Optional[str] = None
        while True:
            if next_msg is None:
                user_msg = console.input("[cyan]user> [/]")
            else:
                user_msg = next_msg
                next_msg = None
            cmd = user_msg.split(maxsplit=1)[0]
            args = user_msg[len(cmd):].strip() if " " in user_msg else ""
            if cmd in {"/exit", "quit", "q"}:
                break
            if cmd in COMMANDS:
                result = COMMANDS[cmd](agent, args)
                if isinstance(result, Agent):
                    agent = result
                continue
            last = agent.run_until_stop(user_msg)
            if last and last.tool_calls:
                for call in last.tool_calls:
                    if call.function.name == "continue":
                        args = json.loads(call.function.arguments or "{}")
                        options = args.get("options")
                        if options:
                            prompt = args.get("prompt", "Choose:")
                            if questionary:
                                next_msg = questionary.select(prompt, choices=options).ask()
                            else:  # pragma: no cover - simple fallback for tests
                                opts = "/".join(options)
                                next_msg = input(f"{prompt} ({opts}): ")
                        break
    finally:
        agent.runtime.cleanup()
