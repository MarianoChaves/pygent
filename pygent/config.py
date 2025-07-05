"""Utilities for loading configuration files."""

import os

import json
try:  # Python 3.11+
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed on older Python versions
    import tomli as tomllib  # type: ignore
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union
import importlib.util
import json

DEFAULT_CONFIG_FILES = [
    Path("pygent.toml"),
    Path.home() / ".pygent.toml",
]


def load_snapshot(path: Union[str, os.PathLike[str]]) -> Path:
    """Load environment variables and history from a snapshot directory."""

    dest = Path(path)
    env_file = dest / "env.json"
    if env_file.is_file():
        try:
            data = json.loads(env_file.read_text())
        except Exception:
            data = {}
        for k, v in data.items():
            os.environ.setdefault(k, str(v))
    ws = dest / "workspace"
    os.environ["PYGENT_WORKSPACE"] = str(ws)
    hist = dest / "history.json"
    if hist.is_file():
        os.environ["PYGENT_HISTORY_FILE"] = str(hist)
    log = dest / "cli.log"
    if log.is_file():
        os.environ["PYGENT_LOG_FILE"] = str(log)
    return ws


def run_py_config(path: Union[str, os.PathLike[str]] = "config.py") -> None:
    """Execute a Python configuration file if it exists."""
    p = Path(path)
    if not p.is_file():
        return
    spec = importlib.util.spec_from_file_location("pygent_config", p)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)


def load_config(path: Optional[Union[str, os.PathLike[str]]] = None) -> Dict[str, Any]:
    """Load configuration from a TOML file and set environment variables.

    Environment variables already set take precedence over file values.
    Returns the configuration dictionary.
    """
    config: Dict[str, Any] = {}
    paths = [Path(path)] if path else DEFAULT_CONFIG_FILES
    for p in paths:
        if p.is_file():
            with p.open("rb") as fh:
                try:
                    data = tomllib.load(fh)
                except Exception:
                    continue
            config.update(data)
    # update environment without overwriting existing values
    if "persona" in config and "PYGENT_PERSONA" not in os.environ:
        os.environ["PYGENT_PERSONA"] = str(config["persona"])
    if "persona_name" in config and "PYGENT_PERSONA_NAME" not in os.environ:
        os.environ["PYGENT_PERSONA_NAME"] = str(config["persona_name"])
    if "task_personas" in config:
        personas = config["task_personas"]
        if isinstance(personas, list) and personas and isinstance(personas[0], Mapping):
            if "PYGENT_TASK_PERSONAS_JSON" not in os.environ:
                os.environ["PYGENT_TASK_PERSONAS_JSON"] = json.dumps(personas)
            if "PYGENT_TASK_PERSONAS" not in os.environ:
                os.environ["PYGENT_TASK_PERSONAS"] = os.pathsep.join(
                    str(p.get("name", "")) for p in personas
                )
        elif "PYGENT_TASK_PERSONAS" not in os.environ:
            if isinstance(personas, list):
                os.environ["PYGENT_TASK_PERSONAS"] = os.pathsep.join(
                    str(p) for p in personas
                )
            else:
                os.environ["PYGENT_TASK_PERSONAS"] = str(personas)
    if "initial_files" in config and "PYGENT_INIT_FILES" not in os.environ:
        if isinstance(config["initial_files"], list):
            os.environ["PYGENT_INIT_FILES"] = os.pathsep.join(
                str(p) for p in config["initial_files"]
            )
        else:
            os.environ["PYGENT_INIT_FILES"] = str(config["initial_files"])
    if "banned_commands" in config and "PYGENT_BANNED_COMMANDS" not in os.environ:
        banned = config["banned_commands"]
        if isinstance(banned, list):
            os.environ["PYGENT_BANNED_COMMANDS"] = os.pathsep.join(str(c) for c in banned)
        else:
            os.environ["PYGENT_BANNED_COMMANDS"] = str(banned)
    if "banned_apps" in config and "PYGENT_BANNED_APPS" not in os.environ:
        apps = config["banned_apps"]
        if isinstance(apps, list):
            os.environ["PYGENT_BANNED_APPS"] = os.pathsep.join(str(a) for a in apps)
        else:
            os.environ["PYGENT_BANNED_APPS"] = str(apps)
    return config
