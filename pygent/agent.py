"""Orchestration layer: receives messages, calls the OpenAI-compatible backend and dispatches tools."""

import json
import os
import pathlib
import uuid
import time
import shutil
import platform
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
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


DEFAULT_MODEL = os.getenv("PYGENT_MODEL", "gpt-4.1-mini")
SYSTEM_MSG = build_system_msg(DEFAULT_PERSONA)

console = Console()


def _default_model() -> Model:
    """Return the global custom model or the default OpenAI model."""
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
    system_msg: str = field(default_factory=lambda: build_system_msg(DEFAULT_PERSONA))
    history: List[Dict[str, Any]] = field(default_factory=list)
    history_file: Optional[pathlib.Path] = field(default_factory=_default_history_file)
    disabled_tools: List[str] = field(default_factory=list)
    log_file: Optional[pathlib.Path] = field(default_factory=_default_log_file)
    confirm_bash: bool = field(default_factory=_default_confirm_bash)

    def __post_init__(self) -> None:
        """Initialize defaults after dataclass construction."""
        self._log_fp = None
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
        if self.log_file is None:
            if hasattr(self.runtime, "base_dir"):
                self.log_file = pathlib.Path(getattr(self.runtime, "base_dir")) / "cli.log"
            else:
                self.log_file = pathlib.Path("cli.log")
        if isinstance(self.log_file, (str, pathlib.Path)):
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
        if self.history_file:
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
                if self.confirm_bash and call.function.name == "bash":
                    args = json.loads(call.function.arguments or "{}")
                    cmd = args.get("cmd", "")
                    console.print(
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
                        ok = questionary.confirm(prompt, default=True).ask()
                    else:  # pragma: no cover - fallback for tests
                        ok_input = console.input(f"{prompt} [Y/n]: ").lower()
                        ok = ok_input == "" or ok_input.startswith("y")
                    if not ok:
                        output = f"$ {cmd}\n[bold red]Aborted by user.[/]"
                        self.append_history({"role": "tool", "content": output, "tool_call_id": call.id})
                        console.print(
                            Panel(
                                output,
                                title=f"[bold red]{self.persona.name} tool:{call.function.name}[/]",
                                border_style="red",
                                box=box.ROUNDED if box else None,
                                title_align="left",
                            )
                        )
                        continue
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
                if call.function.name not in {"ask_user", "stop"}:
                    display_output = output
                    if call.function.name == "read_image" and output.startswith("data:image"):
                        try:
                            args = json.loads(call.function.arguments or "{}")
                            path = args.get("path", "<unknown>")
                        except Exception:
                            path = "<unknown>"
                        display_output = f"returned data URL for {path}"
                    console.print(
                        Panel(
                            display_output,
                            title=f"[bold bright_blue]{self.persona.name} tool:{call.function.name}[/]",
                            border_style="bright_blue",
                            box=box.ROUNDED if box else None,
                            title_align="left",
                        )
                    )
        else:
            markdown_response = Markdown(assistant_msg.content or "") # Ensure content is not None
            console.print(
                Panel(
                    markdown_response,
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
            if any(c.function.name in ("stop", "ask_user") for c in calls):
                break
            msg = "ask_user"

        return last_msg

    def close(self) -> None:
        """Close any open resources."""
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
    preset: Optional[str] = None,
) -> None:  # pragma: no cover
    """Start an interactive session in the terminal.

    Parameters
    ----------
    preset:
        Name of a preset from :data:`pygent.agent_presets.AGENT_PRESETS` to use
        when creating the agent.
    """
    ws = pathlib.Path.cwd() / workspace_name if workspace_name else None
    if preset:
        from .agent_presets import AGENT_PRESETS

        agent = AGENT_PRESETS[preset].create_agent(
            runtime=Runtime(use_docker=use_docker, workspace=ws, banned_commands=banned_commands),
            disabled_tools=disabled_tools or [],
            confirm_bash=bool(confirm_bash) if confirm_bash is not None else _default_confirm_bash(),
        )
    else:
        agent = Agent(
            runtime=Runtime(use_docker=use_docker, workspace=ws, banned_commands=banned_commands),
            disabled_tools=disabled_tools or [],
            confirm_bash=bool(confirm_bash) if confirm_bash is not None else _default_confirm_bash(),
        )
    from .commands import COMMANDS
    mode = "Docker" if agent.runtime.use_docker else "local"
    console.print(
        f"[bold green]{agent.persona.name} ({mode})[/] started. (Type /exit to quit)"
    )
    console.print("Type /help for a list of available commands.")
    try:
        next_msg: Optional[str] = None
        while True:
            if next_msg is None:
                user_msg = console.input("[bold steel_blue]>>> [/]")
            else:
                console.print(f"[bold steel_blue]>>> [/]{next_msg}", highlight=False)
                user_msg = next_msg
                next_msg = None
            if agent._log_fp:
                try:
                    agent._log_fp.write(f"user> {user_msg}\n")
                    agent._log_fp.flush()
                except Exception:
                    pass
            if not user_msg.strip():
                continue
            parts = user_msg.split(maxsplit=1)
            cmd = parts[0]
            args = parts[1] if len(parts) == 2 else ""
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
                    if call.function.name == "ask_user":
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
    except Exception as exc:  # pragma: no cover - interactive only
        from .commands import cmd_save
        dest = pathlib.Path.cwd() / f"crash_{uuid.uuid4().hex[:8]}"
        cmd_save(agent, str(dest))
        console.print(
            Panel(
                f"An unexpected error occurred: [bold red]{exc}[/]\n"
                f"Your workspace has been saved to [cyan]{dest}[/].\n"
                f"You can restore it using: [bold yellow]pygent --load {dest}[/]",
                title="[bold red]Critical Error[/]",
                border_style="red",
                box=box.DOUBLE if box else None,
            )
        )
        # raise # Optionally re-raise the exception if needed for debugging or higher-level handling
    finally:
        console.print("[dim]Closing session...[/]")
        agent.close()
        agent.runtime.cleanup()
