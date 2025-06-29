import os
import tomllib
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_FILES = [
    Path("pygent.toml"),
    Path.home() / ".pygent.toml",
]

def load_config(path: str | os.PathLike[str] | None = None) -> Dict[str, Any]:
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
    if "task_personas" in config and "PYGENT_TASK_PERSONAS" not in os.environ:
        if isinstance(config["task_personas"], list):
            os.environ["PYGENT_TASK_PERSONAS"] = os.pathsep.join(str(p) for p in config["task_personas"])
        else:
            os.environ["PYGENT_TASK_PERSONAS"] = str(config["task_personas"])
    if "initial_files" in config and "PYGENT_INIT_FILES" not in os.environ:
        if isinstance(config["initial_files"], list):
            os.environ["PYGENT_INIT_FILES"] = os.pathsep.join(str(p) for p in config["initial_files"])
        else:
            os.environ["PYGENT_INIT_FILES"] = str(config["initial_files"])
    return config
