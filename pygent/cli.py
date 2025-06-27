"""Command-line entry point for Pygent."""
import argparse

from .agent import run_interactive

def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="pygent")
    parser.add_argument("--docker", dest="use_docker", action="store_true", help="run commands in a Docker container")
    parser.add_argument("--no-docker", dest="use_docker", action="store_false", help="run locally")
    parser.set_defaults(use_docker=None)
    args = parser.parse_args()
    run_interactive(use_docker=args.use_docker)
