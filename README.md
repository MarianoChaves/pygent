# Pygent

Pygent is a coding assistant that executes each request inside an isolated Docker container (meaning the container is discarded after use) whenever possible. If Docker is unavailable (for instance on some Windows setups) the commands are executed locally instead. Full documentation is available in the `docs/` directory and at [pygent-ai.com](https://pygent-ai.com/).

## Features

* Runs commands in ephemeral containers (default image `python:3.12-slim`).
* Integrates with OpenAI-compatible models (models adhering to the OpenAI API specification) to orchestrate each step.
* Persists the conversation history during the session.
* Optionally save the history to a JSON file for later recovery.
* Persist the workspace across sessions by setting `PYGENT_WORKSPACE`.
* Provides a small Python API for use in other projects.
* Optional web interface via `pygent ui` (also available as `pygent-ui`).
* Optional FastAPI server to manage tasks over HTTP.
* Register your own tools and customise the system prompt.
* Extend the CLI with custom commands.
* Build custom interactive sessions by subclassing the `Session` API.
* Execute a `config.py` script on startup for advanced configuration.
* Set environment variables from the command line.
* Each session begins with a short plan that you can approve before execution.
* The assistant can leverage the `bash` tool to run shell commands in a sandboxed environment.

## Installation

The recommended way to install Pygent is using pip:

```bash
pip install pygent
```

To include optional features like Docker support, the web UI, or the FastAPI server, you can specify extras:

```bash
pip install pygent[docker,ui,server]
```

Python ≥ 3.9 is required. The package now bundles the `openai` client for model access.
To run commands in Docker containers, Docker must be installed separately.

If you are a developer or want the latest unreleased changes, you can install from source:

```bash
pip install -e .
```

Python ≥ 3.9 is required. The package now bundles the `openai` client for model access.
To run commands in Docker containers, Docker must be installed separately. If installing from source, you can include Docker support with `pip install -e .[docker,ui,server]`.

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
Pass `--confirm-bash` if you want to approve each bash command before it runs.
Use `--ban-cmd CMD` to disallow specific commands entirely (repeat to ban multiple).
Pass `--config path/to/pygent.toml` to load settings from a file.
Use `--cwd` to run inside the current directory instead of a temporary workspace.

Type messages normally; use `/exit` to end the session. Each command is executed
in the container and the result shown in the terminal.
Interactive programs that expect input (e.g. running `python` without a script)
are not supported and will exit immediately.
For a minimal web interface run `pygent ui` instead (requires `pygent[ui]`).
To expose the API over HTTP run `uvicorn pygent.fastapi_app:create_app` (requires `pygent[server]`).
Use `/help` for a list of built-in commands or `/help <cmd>` for details.
Use `/save DIR` to snapshot the current environment for later use.
Use `/tools` to enable or disable tools during the session.
Use `/banned` to list or update banned commands.
Use `/confirm-bash on|off` to toggle confirmation before running bash commands.
Resume from a snapshot with `pygent --load DIR` or by setting
`PYGENT_SNAPSHOT=DIR`.
Additional commands can be registered programmatically with
`pygent.commands.register_command()`.
The CLI loads a `config.py` script if present (or passed with `--pyconfig`)
and environment variables may be set directly with `-e NAME=value`.


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

You can also override how the assistant builds the system prompt:

```python
from pygent.agent import set_system_message_builder

def my_builder(persona, disabled_tools=None):
    return f"{persona.name}: ready to work"

set_system_message_builder(my_builder)
```

Passing `None` restores the default prompt generation.

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

Use `mkdocs serve` to build the documentation locally and serve it on a local webserver.

## License

This project is released under the MIT license. See the `LICENSE` file for details.

