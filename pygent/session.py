from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
import pathlib
import uuid

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .agent import Agent
from rich.console import Console
try:  # optional rich features
    from rich import __version__ as _rich_version  # noqa: F401
    from rich.panel import Panel
    from rich import box
except Exception:  # pragma: no cover - tests may stub out rich
    import rich as _rich
    if not hasattr(_rich, "__version__"):
        _rich.__version__ = "0"
    if not hasattr(_rich, "__file__"):
        _rich.__file__ = "rich-not-installed"
    Panel = None  # type: ignore
    box = None
try:  # optional dependency
    import questionary  # type: ignore
except Exception:  # pragma: no cover - used in tests without questionary
    questionary = None


class Session(ABC):
    """Abstract interactive session."""

    def __init__(self, agent: Agent) -> None:
        self.agent = agent
        self.console = Console()

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """Return user input for ``prompt``."""

    def ask(self, prompt: str, options: List[str]) -> str:
        """Ask the user to choose from ``options``."""
        return self.get_input(f"{prompt} ({'/'.join(options)}): ")

    def start_message(self) -> None:
        mode = "Docker" if self.agent.runtime.use_docker else "local"
        self.console.print(
            f"[bold green]{self.agent.persona.name} ({mode})[/] started. (Type /exit to quit)"
        )
        self.console.print("Type /help for a list of available commands.")

    def end_session(self) -> None:
        self.console.print("[dim]Closing session...[/]")
        self.agent.close()
        self.agent.runtime.cleanup()

    def run(self) -> None:
        """Run the interactive loop."""
        from .commands import COMMANDS
        # Import Agent lazily to avoid circular import issues
        from .agent import Agent

        self.start_message()
        next_msg: Optional[str] = None
        try:
            while True:
                if next_msg is None:
                    user_msg = self.get_input("[bold steel_blue]>>> [/]")
                else:
                    self.console.print(f"[bold steel_blue]>>> [/]{next_msg}", highlight=False)
                    user_msg = next_msg
                    next_msg = None
                if self.agent._log_fp:
                    try:
                        self.agent._log_fp.write(f"user> {user_msg}\n")
                        self.agent._log_fp.flush()
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
                    result = COMMANDS[cmd](self.agent, args)
                    if isinstance(result, Agent):
                        self.agent = result
                    continue
                last = self.agent.run_until_stop(user_msg)
                if last and last.tool_calls:
                    for call in last.tool_calls:
                        if call.function.name == "ask_user":
                            args = json.loads(call.function.arguments or "{}")
                            options = args.get("options")
                            if options:
                                prompt = args.get("prompt", "Choose:")
                                next_msg = self.ask(prompt, options)
                            break
        except Exception as exc:  # pragma: no cover - interactive only
            from .commands import cmd_save
            dest = pathlib.Path.cwd() / f"crash_{uuid.uuid4().hex[:8]}"
            cmd_save(self.agent, str(dest))
            if Panel:
                self.console.print(
                    Panel(
                        f"An unexpected error occurred: [bold red]{exc}[/]\n"
                        f"Your workspace has been saved to [cyan]{dest}[/].\n"
                        f"You can restore it using: [bold yellow]pygent --load {dest}[/]",
                        title="[bold red]Critical Error[/]",
                        border_style="red",
                        box=box.DOUBLE if box else None,
                    )
                )
            else:  # pragma: no cover - fallback without rich
                print(
                    f"An unexpected error occurred: {exc}\nWorkspace saved to {dest}\n"
                    f"Restore with: pygent --load {dest}"
                )
        finally:
            self.end_session()


class CliSession(Session):
    """Interactive CLI session using ``rich`` and ``questionary`` when available."""

    def get_input(self, prompt: str) -> str:  # pragma: no cover - interactive
        return self.console.input(prompt)

    def ask(self, prompt: str, options: List[str]) -> str:  # pragma: no cover - interactive
        if questionary:
            return questionary.select(prompt, choices=options).ask()
        return super().ask(prompt, options)

