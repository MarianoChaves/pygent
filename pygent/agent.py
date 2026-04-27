"""Orchestration layer: receives messages, calls the model, and dispatches tools."""

import json
import os
import pathlib
import time
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

try:
    from rich import __version__ as _rich_version  # noqa: F401
except Exception:  # pragma: no cover - tests may stub out rich
    import rich as _rich

    if not hasattr(_rich, "__version__"):
        _rich.__version__ = "0"
    if not hasattr(_rich, "__file__"):
        _rich.__file__ = "rich-not-installed"

try:
    from rich import box  # type: ignore
except Exception:  # pragma: no cover - tests may stub out rich
    box = None

try:  # pragma: no cover - optional dependency
    import questionary  # type: ignore
except Exception:  # pragma: no cover - used in tests without questionary
    questionary = None

from . import models, openai_compat, tools
from .models import Model, OpenAIModel
from .persona import Persona
from .runtime import Runtime
from .session import CliSession
from .system_message import DEFAULT_PERSONA, build_system_msg

DEFAULT_MODEL = os.getenv("PYGENT_MODEL", "gpt-4.1-mini")
console = Console()


def _safe_print(*args: Any, **kwargs: Any) -> None:
    if console is not None and hasattr(console, "print"):
        console.print(*args, **kwargs)


def _status(message: str, spinner: str):
    if console is not None and hasattr(console, "status"):
        return console.status(message, spinner=spinner)
    return nullcontext()


def _default_model() -> Model:
    return models.CUSTOM_MODEL or OpenAIModel()


def _default_history_file() -> Optional[pathlib.Path]:
    env = os.getenv("PYGENT_HISTORY_FILE")
    return pathlib.Path(env) if env else None


def _default_log_file() -> Optional[pathlib.Path]:
    env = os.getenv("PYGENT_LOG_FILE")
    return pathlib.Path(env) if env else None


def _default_confirm_bash() -> bool:
    return os.getenv("PYGENT_CONFIRM_BASH", "1") not in {"", "0", "false", "False"}


@dataclass
class Agent:
    """Interactive assistant handling messages and tool execution."""

    runtime: Runtime = field(default_factory=Runtime)
    model: Model = field(default_factory=_default_model)
    model_name: str = DEFAULT_MODEL
    persona: Persona = field(default_factory=lambda: DEFAULT_PERSONA)
    system_message_builder: Optional[Callable[[Persona, Optional[List[str]]], str]] = None
    system_msg: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    history_file: Optional[pathlib.Path] = field(default_factory=_default_history_file)
    disabled_tools: List[str] = field(default_factory=list)
    log_file: Optional[pathlib.Path] = field(default_factory=_default_log_file)
    confirm_bash: bool = field(default_factory=_default_confirm_bash)
    max_non_tool_replies: Optional[int] = None

    def __post_init__(self) -> None:
        self._log_fp = None
        if not self.system_msg:
            self.refresh_system_message()
        self._restore_history_file()
        if not self.history:
            self.append_history({"role": "system", "content": self.system_msg})
        self._init_log_file()

    def _restore_history_file(self) -> None:
        if not self.history_file or not isinstance(self.history_file, (str, pathlib.Path)):
            return
        self.history_file = pathlib.Path(self.history_file)
        if not self.history_file.is_file():
            return
        try:
            with self.history_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            data = []
        self.history = [openai_compat.parse_message(m) if isinstance(m, dict) else m for m in data]

    def _init_log_file(self) -> None:
        if self.log_file is None:
            base_dir = getattr(self.runtime, "base_dir", None)
            self.log_file = pathlib.Path(base_dir) / "cli.log" if base_dir else pathlib.Path("cli.log")
        if not isinstance(self.log_file, (str, pathlib.Path)):
            return
        self.log_file = pathlib.Path(self.log_file)
        os.environ.setdefault("PYGENT_LOG_FILE", str(self.log_file))
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._log_fp = self.log_file.open("a", encoding="utf-8")
        except Exception:
            self._log_fp = None

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
        if not self.history_file:
            return
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with self.history_file.open("w", encoding="utf-8") as fh:
            json.dump([self._message_dict(m) for m in self.history], fh)

    def append_history(self, msg: Any) -> None:
        self.history.append(msg)
        self._save_history()
        if self._log_fp:
            try:
                self._log_fp.write(json.dumps(self._message_dict(msg)) + "\n")
                self._log_fp.flush()
            except Exception:
                pass

    def refresh_system_message(self) -> None:
        if self.system_message_builder:
            self.system_msg = self.system_message_builder(self.persona, self.disabled_tools)
        else:
            self.system_msg = build_system_msg(self.persona, self.disabled_tools)
        if self.history and self.history[0].get("role") == "system":
            self.history[0]["content"] = self.system_msg

    def _active_schemas(self) -> List[Dict[str, Any]]:
        return [
            schema
            for schema in tools.TOOL_SCHEMAS
            if schema["function"]["name"] not in self.disabled_tools
        ]

    def _confirm_bash_call(self, call: openai_compat.ToolCall) -> bool:
        if not (self.confirm_bash and call.function.name == "bash"):
            return True
        args = json.loads(call.function.arguments or "{}")
        cmd = args.get("cmd", "")
        _safe_print(
            Panel(
                f"$ {cmd}",
                title=f"[bold yellow]{self.persona.name} pending bash[/]",
                border_style="yellow",
                box=box.HEAVY_HEAD if box else None,
                title_align="left",
            )
        )
        prompt = "Run this command?"
        if questionary:
            approved = questionary.confirm(prompt, default=True).ask()
        elif console is not None and hasattr(console, "input"):  # pragma: no cover - fallback for tests
            answer = console.input(f"{prompt} [Y/n]: ").lower()
            approved = answer == "" or answer.startswith("y")
        else:
            approved = False
        if approved:
            return True

        output = f"$ {cmd}\n[bold red]Aborted by user.[/]"
        self.append_history({"role": "tool", "content": output, "tool_call_id": call.id})
        _safe_print(
            Panel(
                output,
                title=f"[bold red]{self.persona.name} tool:{call.function.name}[/]",
                border_style="red",
                box=box.ROUNDED if box else None,
                title_align="left",
            )
        )
        return False

    def _display_tool_output(self, call: openai_compat.ToolCall, output: str) -> None:
        if call.function.name in {"ask_user", "stop"}:
            return

        display_output = output
        if call.function.name == "read_image" and output.startswith("data:image"):
            try:
                args = json.loads(call.function.arguments or "{}")
                path = args.get("path", "<unknown>")
                self.append_history(
                    {
                        "role": "user",
                        "content": [{"type": "image_url", "image_url": {"url": output}}],
                    }
                )
            except Exception:
                path = "<unknown>"
            display_output = f"returned data URL for {path}"

        _safe_print(
            Panel(
                display_output,
                title=f"[bold bright_blue]{self.persona.name} tool:{call.function.name}[/]",
                border_style="bright_blue",
                box=box.ROUNDED if box else None,
                title_align="left",
            )
        )

    def _execute_tool_call(self, call: openai_compat.ToolCall) -> None:
        if not self._confirm_bash_call(call):
            return
        with _status(f"[green]Running {call.function.name}...", spinner="line"):
            output = tools.execute_tool(call, self.runtime)
        self.append_history({"role": "tool", "content": output, "tool_call_id": call.id})
        self._display_tool_output(call, output)

    def step(self, user_msg: str = None, role: str = "user") -> openai_compat.Message:
        """Execute one round of interaction with the model."""

        self.refresh_system_message()
        if user_msg:
            self.append_history({"role": role, "content": user_msg})

        with _status("[bold cyan]Thinking...", spinner="dots"):
            assistant_raw = self.model.chat(self.history, self.model_name, self._active_schemas())

        assistant_msg = openai_compat.parse_message(assistant_raw)
        self.append_history(assistant_msg)

        if assistant_msg.tool_calls:
            for call in assistant_msg.tool_calls:
                self._execute_tool_call(call)
        else:
            _safe_print(
                Panel(
                    Markdown(assistant_msg.content or ""),
                    title=f"[bold green]{self.persona.name} replied[/]",
                    title_align="left",
                    border_style="green",
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

        msg: Optional[str] = user_msg
        start = time.monotonic()
        self._timed_out = False
        last_msg = None
        non_tool_replies = 0

        for idx in range(max_steps):
            if max_time is not None and time.monotonic() - start > max_time:
                self.append_history({"role": "system", "content": f"[timeout after {max_time}s]"})
                self._timed_out = True
                break

            step_start = time.monotonic()
            role = "user" if idx == 0 else "system"
            assistant_msg = self.step(msg, role=role)
            last_msg = assistant_msg

            if step_timeout is not None and time.monotonic() - step_start > step_timeout:
                self.append_history({"role": "system", "content": f"[timeout after {step_timeout}s]"})
                self._timed_out = True
                break

            calls = assistant_msg.tool_calls or []
            if any(c.function.name in ("stop", "ask_user") for c in calls):
                break

            if calls:
                non_tool_replies = 0
            else:
                non_tool_replies += 1
                if self.max_non_tool_replies is not None and non_tool_replies >= self.max_non_tool_replies:
                    self.append_history(
                        {"role": "system", "content": "[stopped after too many non-tool replies]"}
                    )
                    break
            msg = None

        return last_msg

    def close(self) -> None:
        if self._log_fp:
            try:
                self._log_fp.close()
            finally:
                self._log_fp = None


def run_interactive(
    use_docker: Optional[bool] = None,
    workspace_name: Optional[str] = None,
    disabled_tools: Optional[List[str]] = None,
    confirm_bash: Optional[bool] = None,
    banned_commands: Optional[List[str]] = None,
) -> None:  # pragma: no cover
    """Start an interactive session in the terminal."""

    ws = pathlib.Path.cwd() / workspace_name if workspace_name else None
    agent = Agent(
        runtime=Runtime(use_docker=use_docker, workspace=ws, banned_commands=banned_commands),
        disabled_tools=disabled_tools or [],
        confirm_bash=bool(confirm_bash) if confirm_bash is not None else _default_confirm_bash(),
    )
    CliSession(agent).run()
