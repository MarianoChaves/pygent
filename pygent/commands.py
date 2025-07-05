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


class Command:
    """CLI command definition."""

    def __init__(self, handler: Callable[[Agent, str], Optional[Agent]], description: str | None = None):
        self.handler = handler
        self.description = description or (handler.__doc__ or "")

    def __call__(self, agent: Agent, arg: str) -> Optional[Agent]:
        return self.handler(agent, arg)


def cmd_cmd(agent: Agent, arg: str) -> None:
    """Run a raw shell command in the sandbox."""
    output = agent.runtime.bash(arg)
    print(output)


def cmd_cp(agent: Agent, arg: str) -> None:
    """Copy a file into the workspace: ``/cp SRC [DEST]``."""
    parts = arg.split()
    if not parts:
        print("usage: /cp SRC [DEST]")
        return
    src = parts[0]
    dest = parts[1] if len(parts) > 1 else None
    msg = agent.runtime.upload_file(src, dest)
    print(msg)


def cmd_new(agent: Agent, arg: str) -> Agent:
    """Restart the conversation with a fresh history."""
    persistent = agent.runtime._persistent
    use_docker = agent.runtime.use_docker
    workspace = agent.runtime.base_dir if persistent else None
    agent.runtime.cleanup()
    return Agent(runtime=Runtime(use_docker=use_docker, workspace=workspace))


def cmd_help(agent: Agent, arg: str) -> None:
    """Display available commands."""
    if arg:
        cmd = COMMANDS.get(arg)
        if cmd:
            print(f"{arg} - {cmd.description}")
        else:
            print(f"No help available for {arg}")
        return

    print("Available commands:")
    for name, command in sorted(COMMANDS.items()):
        print(f"  {name:<5} - {command.description}")
    print("  /exit - quit the session")


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


def register_command(name: str, handler: Callable[[Agent, str], Optional[Agent]], description: str | None = None) -> None:
    """Register a custom CLI command."""
    if name in COMMANDS:
        raise ValueError(f"command {name} already registered")
    COMMANDS[name] = Command(handler, description)


COMMANDS = {
    "/cmd": Command(cmd_cmd),
    "/cp": Command(cmd_cp),
    "/new": Command(cmd_new),
    "/help": Command(cmd_help),
    "/save": Command(cmd_save),
    "/tools": Command(cmd_tools),
    "/banned": Command(cmd_banned),
}
