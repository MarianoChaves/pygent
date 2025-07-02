"""Interactive CLI session using prompt_toolkit."""
from __future__ import annotations

import pathlib
from typing import Optional

from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from .agent import Agent
from .runtime import Runtime
from .commands import COMMANDS


class InteractiveSession:
    """Handle user interaction in the terminal."""

    def __init__(self, use_docker: Optional[bool] = None, workspace: Optional[str] = None) -> None:
        ws = pathlib.Path.cwd() / workspace if workspace else None
        self.agent = Agent(runtime=Runtime(use_docker=use_docker, workspace=ws))
        history_path = pathlib.Path.home() / ".pygent_history"
        self.session = PromptSession(history=FileHistory(str(history_path)))
        self.console = Console()

    def start(self) -> None:
        mode = "Docker" if self.agent.runtime.use_docker else "local"
        self.console.print(
            f"[bold green]{self.agent.persona.name} ({mode})[/] iniciado. (digite /exit para sair)"
        )
        try:
            while True:
                user_msg = self.session.prompt("[cyan]user> ")
                if not user_msg:
                    continue
                cmd = user_msg.split(maxsplit=1)[0]
                args = user_msg[len(cmd):].strip() if " " in user_msg else ""
                if cmd in {"/exit", "quit", "q"}:
                    break
                if cmd in COMMANDS:
                    result = COMMANDS[cmd](self.agent, args)
                    if isinstance(result, Agent):
                        self.agent = result
                    continue
                self.agent.run_until_stop(user_msg)
        finally:
            self.agent.runtime.cleanup()
