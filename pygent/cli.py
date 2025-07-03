"""Command-line interface for Pygent using ``typer``."""

from __future__ import annotations

from typing import Optional, List

import typer

from .config import load_config


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
    omit_tool: List[str] = typer.Option(
        None,
        "--omit-tool",
        help="disable a specific tool",
        show_default=False,
    ),
) -> None:  # pragma: no cover - CLI wrapper
    """Start an interactive session when no subcommand is given."""
    load_config(config)
    ctx.obj = {"docker": docker, "workspace": workspace, "omit_tool": omit_tool or []}
    if ctx.invoked_subcommand is None:
        from .agent import run_interactive

        run_interactive(use_docker=docker, workspace_name=workspace, disabled_tools=omit_tool or [])
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

