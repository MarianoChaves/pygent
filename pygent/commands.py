from __future__ import annotations

"""Simple command handlers for the interactive CLI."""

from typing import Callable, Optional

from .agent import Agent
from .runtime import Runtime


class Command:
    """CLI command definition."""

    def __init__(self, handler: Callable[[Agent, str], Optional[Agent]]):
        self.handler = handler

    def __call__(self, agent: Agent, arg: str) -> Optional[Agent]:
        return self.handler(agent, arg)


def cmd_cmd(agent: Agent, arg: str) -> None:
    output = agent.runtime.bash(arg)
    print(output)


def cmd_cp(agent: Agent, arg: str) -> None:
    parts = arg.split()
    if not parts:
        print("usage: /cp SRC [DEST]")
        return
    src = parts[0]
    dest = parts[1] if len(parts) > 1 else None
    msg = agent.runtime.upload_file(src, dest)
    print(msg)


def cmd_new(agent: Agent, arg: str) -> Agent:
    persistent = agent.runtime._persistent
    use_docker = agent.runtime.use_docker
    workspace = agent.runtime.base_dir if persistent else None
    agent.runtime.cleanup()
    return Agent(runtime=Runtime(use_docker=use_docker, workspace=workspace))


COMMANDS = {
    "/cmd": Command(cmd_cmd),
    "/cp": Command(cmd_cp),
    "/new": Command(cmd_new),
}
