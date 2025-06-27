# Pygent

Pygent is a coding assistant that executes each request inside an isolated Docker container whenever possible. If Docker is unavailable (for instance on some Windows setups) the commands are executed locally instead.

## Features

* Runs commands in ephemeral containers (default image `python:3.12-slim`).
* Integrates with OpenAI-compatible models to orchestrate each step.
* Persists the conversation history during the session.
* Provides a small Python API for use in other projects.

## Installation

Installing from source is recommended:

```bash
pip install -e .
```

Python ≥ 3.9 is required. The only runtime dependency is `rich`.
Install any OpenAI-compatible library such as `openai` or `litellm` separately to enable model access.
To run commands in Docker containers also install `pygent[docker]`.

## Configuration

Behaviour can be adjusted via environment variables:

* `OPENAI_API_KEY` &ndash; key used to access the OpenAI API.
* `PYGENT_MODEL` &ndash; model name used for requests (default `gpt-4o-mini-preview`).
* `PYGENT_IMAGE` &ndash; Docker image to create the container (default `python:3.12-slim`).
* `PYGENT_USE_DOCKER` &ndash; set to `0` to disable Docker and run locally.

## CLI usage

After installing run:

```bash
pygent
```

Use `--docker` to run commands inside a container (requires
`pygent[docker]`). Use `--no-docker` or set `PYGENT_USE_DOCKER=0`
to force local execution.

Type messages normally; use `/exit` to end the session. Each command is executed in the container and the result shown in the terminal.

## API usage

You can also interact directly with the Python code:

```python
from pygent import Agent

ag = Agent()
ag.step("echo 'Hello World'")
# ... more steps
ag.runtime.cleanup()
```

See the `examples/` folder for more complete scripts.

## Development

1. Install the test dependencies:

```bash
pip install -e .[test]
```

2. Run the test suite:

```bash
pytest
```

Use `mkdocs serve` to build the documentation locally.

## License

This project is released under the MIT license. See the `LICENSE` file for details.

