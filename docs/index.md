# Pygent

Pygent is a minimal coding assistant that runs tasks inside an isolated Docker container whenever available. If Docker is not configured the commands run locally. This manual summarises the main commands and configuration options. See [Configuration](configuration.md) for a list of environment variables.

The latest version of this guide is published online at [marianochaves.github.io/pygent](https://marianochaves.github.io/pygent/).
See the [Examples](examples.md) section for runnable scripts.

See [Getting Started](getting-started.md) for a quick tutorial or jump to the [API Reference](api-reference.md) for details about the available classes.

## Installation

```bash
pip install pygent
```

Python ≥ 3.9 is required. Docker is optional; install `pygent[docker]` to enable container execution. The default model is `gpt-4.1-mini`.

## Basic usage

Start an interactive session by running `pygent` in the terminal. Use the `--docker` option to run commands in a container (requires `pygent[docker]`); otherwise they execute locally. Use `/exit` to quit.
Pass `--config path/to/pygent.toml` to load settings from a file.
Alternatively run `pygent-ui` for a simple web interface (requires `pygent[ui]`).

You can also use the Python API:

```python
from pygent import Agent
ag = Agent()
ag.step("echo test")
ag.runtime.cleanup()
```

Custom models are supported by implementing the ``Model`` protocol and passing
the instance to ``Agent``.

## Development

Install optional dependencies with `pip install -e .[test,docs]` and run `pytest` to execute the tests. Use `mkdocs serve` to build this documentation locally.

See the README file for more detailed information.
