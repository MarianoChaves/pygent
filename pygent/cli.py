"""Command-line interface for Pygent using ``typer``."""

from __future__ import annotations

from typing import Optional, List
import os

import typer

from .config import load_config, run_py_config, load_snapshot
from .agent_presets import AGENT_PRESETS


app = typer.Typer(invoke_without_command=True, help="Pygent command line interface")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    docker: Optional[bool] = typer.Option(
        None,
        "--docker/--no-docker",
        help="run commands in a Docker container",
    ),
    config: Optional[str] = typer.Option(
        None,
        "-c",
        "--config",
        help="path to configuration file",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "-w",
        "--workspace",
        help="name of workspace directory",
    ),
    cwd: bool = typer.Option(
        False,
        "--cwd",
        help="use the current directory as workspace",
    ),
    pyconfig: Optional[str] = typer.Option(
        None,
        "--pyconfig",
        help="path to Python config file to execute",
    ),
    env: List[str] = typer.Option(
        None,
        "-e",
        "--env",
        help="set environment variable",
        show_default=False,
    ),
    load: Optional[str] = typer.Option(
        None,
        "--load",
        help="load snapshot directory",
    ),
    omit_tool: List[str] = typer.Option(
        None,
        "--omit-tool",
        help="disable a specific tool",
        show_default=False,
    ),
    confirm_bash: Optional[bool] = typer.Option(
        None,
        "--confirm-bash/--no-confirm-bash",
        help="ask confirmation before running bash commands",
    ),
    ban_cmd: List[str] = typer.Option(
        None,
        "--ban-cmd",
        help="command to ban (repeatable)",
        show_default=False,
    ),
    preset: Optional[str] = typer.Option(
        None,
        "--preset",
        help="start session using a predefined agent preset (autonomous, assistant, reviewer)",
        show_default=False,
    ),
) -> None:  # pragma: no cover - CLI wrapper
    """Start an interactive session when no subcommand is given."""
    load_config(config)
    if load is None:
        load = os.getenv("PYGENT_SNAPSHOT")
    if load:
        workspace = str(load_snapshot(load))
    for item in env or []:
        if "=" in item:
            key, val = item.split("=", 1)
            os.environ[key] = val
    if cwd:
        workspace = os.getcwd()
    if pyconfig:
        run_py_config(pyconfig)
    else:
        run_py_config("config.py")
    ctx.obj = {
        "docker": docker,
        "workspace": workspace,
        "omit_tool": omit_tool or [],
        "confirm_bash": confirm_bash,
        "ban_cmd": ban_cmd or [],
        "preset": preset,
    }
    if ctx.invoked_subcommand is None:
        from .agent import run_interactive

        run_interactive(
            use_docker=docker,
            workspace_name=workspace,
            disabled_tools=omit_tool or [],
            confirm_bash=confirm_bash,
            banned_commands=ban_cmd or [],
            preset=preset,
        )
        raise typer.Exit()


@app.command()
def ui(ctx: typer.Context) -> None:  # pragma: no cover - optional
    """Launch the simple web interface."""

    from .ui import run_gui

    run_gui(use_docker=ctx.obj.get("docker"))


@app.command()
def version() -> None:  # pragma: no cover - trivial
    """Print the installed version."""

    from . import __version__

    typer.echo(__version__)


def run() -> None:  # pragma: no cover
    """Entry point for the ``pygent`` script."""

    app()


main = run  # Backwards compatibility

