# Pygent

Pygent is a coding assistant that executes each request inside an isolated Docker container whenever possible. If Docker is unavailable (for instance on some Windows setups) the commands are executed locally instead. Full documentation is available in the `docs/` directory and at [marianochaves.github.io/pygent](https://marianochaves.github.io/pygent/).

## Features

* Runs commands in ephemeral containers (default image `python:3.12-slim`).
* Integrates with OpenAI-compatible models to orchestrate each step.
* Persists the conversation history during the session.
* Optionally save the history to a JSON file for later recovery.
* Persist the workspace across sessions by setting `PYGENT_WORKSPACE`.
* Provides a small Python API for use in other projects.
* Optional web interface via `pygent-ui`.
* Register your own tools and customise the system prompt.

## Installation

Installing from source is recommended:

```bash
pip install -e .
```

Python ≥ 3.9 is required. The package now bundles the `openai` client for model access.
To run commands in Docker containers also install `pygent[docker]`.

## Configuration

Behaviour can be adjusted via environment variables (see `docs/configuration.md` for a complete list):

* `OPENAI_API_KEY` &ndash; key used to access the OpenAI API.
  Set this to your API key or a key from any compatible provider.
* `OPENAI_BASE_URL` &ndash; base URL for OpenAI-compatible APIs
  (defaults to ``https://api.openai.com/v1``).
* `PYGENT_MODEL` &ndash; model name used for requests (default `gpt-4.1-mini`).
* `PYGENT_IMAGE` &ndash; Docker image to create the container (default `python:3.12-slim`).
* `PYGENT_USE_DOCKER` &ndash; set to `0` to disable Docker and run locally.
* `PYGENT_MAX_TASKS` &ndash; maximum number of concurrent delegated tasks (default `3`).

Settings can also be read from a `pygent.toml` file. See
[examples/sample_config.toml](https://github.com/marianochaves/pygent/blob/main/examples/sample_config.toml)
and the accompanying
[config_file_example.py](https://github.com/marianochaves/pygent/blob/main/examples/config_file_example.py)
script for a working demonstration that generates tests using a delegated agent.

## CLI usage

After installing run:

```bash
pygent
```

Use `--docker` to run commands inside a container (requires
`pygent[docker]`). Use `--no-docker` or set `PYGENT_USE_DOCKER=0`
to force local execution. When the session starts the CLI shows the
persona name and whether it is running locally or in Docker so you
can easily tell which agent is active.
Pass `--config path/to/pygent.toml` to load settings from a file.

Type messages normally; use `/exit` to end the session. Each command is executed
in the container and the result shown in the terminal.
Interactive programs that expect input (e.g. running `python` without a script)
are not supported and will exit immediately.
For a minimal web interface run `pygent-ui` instead (requires `pygent[ui]`).


## API usage

You can also interact directly with the Python code:

```python
from pygent import Agent

ag = Agent()
ag.step("echo 'Hello World'")
# ... more steps
ag.runtime.cleanup()
```

See the [examples](https://github.com/marianochaves/pygent/tree/main/examples) folder for more complete scripts. Models can be swapped by
passing an object implementing the ``Model`` interface when creating the
``Agent``. The default uses an OpenAI-compatible API, but custom models are
easy to plug in. They can also trigger tools by returning a message with
``tool_calls`` as demonstrated in ``examples/custom_model_with_tool.py``.

Custom models can also be configured globally:

```python
from pygent.models import set_custom_model
set_custom_model(MyModel())
```

All new agents and delegated tasks will use this model unless another one is passed explicitly.

### Using OpenAI and other providers

Set your OpenAI key:

```bash
export OPENAI_API_KEY="sk-..."
```

To use a different provider, set `OPENAI_BASE_URL` to the provider
endpoint and keep `OPENAI_API_KEY` pointing to the correct key:

```bash
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_API_KEY="your-provider-key"
```

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

