from __future__ import annotations

"""Simple command handlers for the interactive CLI."""

from typing import Callable, Optional, Dict

import os
import json
import shutil
from pathlib import Path

from .agent import Agent
from .runtime import Runtime
from . import tools

from rich.console import Console
try:  # optional rich features
    from rich import __version__ as _rich_version  # noqa: F401
    from rich.table import Table
    from rich.text import Text
except Exception:  # pragma: no cover - tests may stub out rich
    import rich as _rich
    if not hasattr(_rich, "__version__"):
        _rich.__version__ = "0"
    if not hasattr(_rich, "__file__"):
        _rich.__file__ = "rich-not-installed"
    Table = None  # type: ignore
    Text = None  # type: ignore


class Command:
    """CLI command definition."""

    def __init__(self, handler: Callable[[Agent, str], Optional[Agent]], description: str | None = None, usage: str | None = None):
        self.handler = handler
        self.description = description or (handler.__doc__ or "")
        self.usage = usage

    def __call__(self, agent: Agent, arg: str) -> Optional[Agent]:
        return self.handler(agent, arg)


def cmd_cmd(agent: Agent, arg: str) -> None:
    """Run a raw shell command in the sandbox."""
    console = Console()

    def _stream(line: str) -> None:
        console.print(line, end="")

    agent.runtime.bash(arg, stream=_stream)


def cmd_cp(agent: Agent, arg: str) -> None:
    """Copy a file into the workspace."""
    parts = arg.split()
    console = Console()
    if not parts:
        console.print("Usage: /cp SRC [DEST]", style="bold red")
        return
    src = parts[0]
    dest = parts[1] if len(parts) > 1 else None
    try:
        msg = agent.runtime.upload_file(src, dest)
        console.print(msg)
    except Exception as e:
        console.print(f"Error: {e}", style="bold red")


def cmd_new(agent: Agent, arg: str) -> Agent:
    """Restart the conversation with a fresh history."""
    persistent = agent.runtime._persistent
    use_docker = agent.runtime.use_docker
    workspace = agent.runtime.base_dir if persistent else None
    agent.runtime.cleanup()
    console = Console()
    console.print("Starting a new session.", style="green")
    return Agent(runtime=Runtime(use_docker=use_docker, workspace=workspace))


def cmd_help(agent: Agent, arg: str) -> None:
    """Display available commands."""
    console = Console()

    if arg:
        command_name = arg if arg.startswith('/') else f'/{arg}'
        cmd = COMMANDS.get(command_name)
        if not cmd:
            console.print(f"No help available for {arg}", style="bold red")
            return
        if Table and Text:
            table = Table(title=f"Help: {command_name}", show_header=False, box=None, padding=(0, 2))
            table.add_row(Text("Description:", style="bold cyan"), cmd.description)
            if cmd.usage:
                table.add_row(Text("Usage:", style="bold cyan"), cmd.usage)
            else:
                table.add_row(Text("Usage:", style="bold cyan"), command_name)
            console.print(table)
        else:  # plain fallback
            print(f"{command_name} - {cmd.description}")
            print(f"Usage: {cmd.usage or command_name}")
        return

    if Table and Text:
        table = Table(title="Available Commands", title_style="bold magenta", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="dim", width=15)
        table.add_column("Description")
        table.add_column("Usage", width=30)

        for name, command in sorted(COMMANDS.items()):
            usage = command.usage or name
            table.add_row(name, command.description, usage)
        table.add_row("/exit", "Quit the session.", "/exit")

        console.print(table)
    else:
        print("Available Commands:")
        for name, command in sorted(COMMANDS.items()):
            usage = command.usage or name
            print(f"{name} - {command.description} ({usage})")
        print("/exit - quit the session (/exit)")


def cmd_save(agent: Agent, arg: str) -> None:
    """Save workspace and environment to ``DIR`` for later use."""
    if not arg:
        print("usage: /save DIR")
        return
    dest = Path(arg).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    agent.runtime.export_file(".", dest / "workspace")
    if agent.history_file and agent.history_file.exists():
        shutil.copy(agent.history_file, dest / "history.json")
    env = {k: v for k, v in os.environ.items() if k.startswith(("PYGENT_", "OPENAI_"))}
    (dest / "env.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    if agent.log_file and Path(agent.log_file).exists():
        shutil.copy(agent.log_file, dest / "cli.log")
    print(f"Saved environment to {dest}")


def cmd_tools(agent: Agent, arg: str) -> None:
    """Enable/disable tools at runtime or list them."""
    parts = arg.split()
    if not parts or parts[0] == "list":
        for name in sorted(tools.TOOLS):
            suffix = " (disabled)" if name in agent.disabled_tools else ""
            print(f"{name}{suffix}")
        return
    if len(parts) != 2 or parts[0] not in {"enable", "disable"}:
        print("usage: /tools [list|enable NAME|disable NAME]")
        return
    action, name = parts
    if action == "enable":
        if name in agent.disabled_tools:
            agent.disabled_tools.remove(name)
            agent.refresh_system_message()
            print(f"Enabled {name}")
        else:
            print(f"{name} already enabled")
    else:
        if name not in agent.disabled_tools:
            agent.disabled_tools.append(name)
            agent.refresh_system_message()
            print(f"Disabled {name}")
        else:
            print(f"{name} already disabled")


def cmd_banned(agent: Agent, arg: str) -> None:
    """List or modify banned commands."""
    parts = arg.split()
    if not parts or parts[0] == "list":
        for name in sorted(agent.runtime.banned_commands):
            print(name)
        return
    if len(parts) != 2 or parts[0] not in {"add", "remove"}:
        print("usage: /banned [list|add CMD|remove CMD]")
        return
    action, name = parts
    if action == "add":
        agent.runtime.banned_commands.add(name)
        print(f"Added {name}")
    else:
        if name in agent.runtime.banned_commands:
            agent.runtime.banned_commands.remove(name)
            print(f"Removed {name}")
        else:
            print(f"{name} not banned")


def cmd_confirm_bash(agent: Agent, arg: str) -> None:
    """Show or toggle confirmation for bash commands."""
    arg = arg.strip().lower()
    if not arg:
        status = "on" if agent.confirm_bash else "off"
        print(status)
        return
    if arg not in {"on", "off"}:
        print("usage: /confirm-bash [on|off]")
        return
    agent.confirm_bash = arg == "on"
    print("confirmation " + ("enabled" if agent.confirm_bash else "disabled"))


def register_command(
    name: str,
    handler: Callable[[Agent, str], Optional[Agent]],
    description: str | None = None,
    usage: str | None = None,
) -> None:
    """Register a custom CLI command."""
    if name in COMMANDS:
        raise ValueError(f"command {name} already registered")
    COMMANDS[name] = Command(handler, description, usage)


COMMANDS: Dict[str, Command] = {
    "/cmd": Command(cmd_cmd, description="Run a raw shell command in the sandbox.", usage="/cmd <command>"),
    "/cp": Command(cmd_cp, description="Copy a file into the workspace.", usage="/cp SRC [DEST]"),
    "/new": Command(cmd_new, description="Restart the conversation with a fresh history.", usage="/new"),
    "/help": Command(cmd_help, description="Display available commands.", usage="/help [command]"),
    "/save": Command(cmd_save, description="Save workspace and environment to DIR for later use.", usage="/save DIR"),
    "/tools": Command(cmd_tools, description="Enable/disable tools at runtime or list them.", usage="/tools [list|enable NAME|disable NAME]"),
    "/banned": Command(cmd_banned, description="List or modify banned commands.", usage="/banned [list|add CMD|remove CMD]"),
    "/confirm-bash": Command(cmd_confirm_bash, description="Toggle confirmation before running bash commands.", usage="/confirm-bash [on|off]"),
}
