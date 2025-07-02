"""Command-line interface for Pygent using Typer."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .config import load_config
from .agent import run_interactive

app = typer.Typer(add_completion=False, help="Pygent - assistente de c\u00f3digo")


@app.callback(invoke_without_command=True)
def cli(
    ctx: typer.Context,
    docker: Optional[bool] = typer.Option(
        None,
        "--docker/--no-docker",
        help="run commands in a Docker container",
    ),
    config: Optional[Path] = typer.Option(
        None, "-c", "--config", help="path to configuration file"
    ),
    workspace: Optional[Path] = typer.Option(
        None, "-w", "--workspace", help="name of workspace directory"
    ),
) -> None:
    """Start an interactive session if no subcommand is given."""
    load_config(str(config) if config else None)
    if ctx.invoked_subcommand is None:
        run_interactive(
            use_docker=docker, workspace_name=str(workspace) if workspace else None
        )


def main() -> None:  # pragma: no cover
    """Entry point for the ``pygent`` console script."""
    app()


if __name__ == "__main__":  # pragma: no cover
    app()
