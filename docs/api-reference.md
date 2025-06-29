# API Reference

This section summarises the most relevant classes and functions.

## `Agent`

```python
from pygent import Agent
```

Manages the conversation with the model. Each instance owns a
`Runtime` accessible via ``agent.runtime``.

**Methods**

- `step(user_msg: str) -> None` – add a message, run tools and print
  their output.
- `run_interactive(use_docker: bool | None = None) -> None` – start an
  interactive session.
- `run_gui(use_docker: bool | None = None) -> None` – start a simple
  web interface.

## `Runtime`

Executes commands either in a Docker container or locally.

**Methods**

- `bash(cmd: str, timeout: int = 30) -> str` – run a shell command and
  return its output.
- `write_file(path: str, content: str) -> str` – create or replace a
  UTF-8 encoded text file in the working directory.
- `cleanup() -> None` – destroy the temporary workspace and stop the
  container if used.

## Tools

Two tools are available by default:

- **bash** &ndash; executes shell commands via `Runtime.bash`.
- **write_file** &ndash; writes files through `Runtime.write_file`.

Additional tools can be registered programmatically using
`pygent.register_tool` or the `pygent.tool` decorator. Each tool receives the
active `Runtime` instance and must return a string.

```python
from pygent import register_tool

def hello(rt, name: str) -> str:
    return f"Hello {name}!"

register_tool(
    "hello",
    "Greet the user",
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    hello,
)
```

Refer to the `tools.py` module for more details.

## Custom prompts

Pass a custom string to the `Agent` constructor to override the system prompt:

```python
from pygent import Agent
ag = Agent(system_msg="You are a friendly bot")
```

## Custom models

The `Agent` relies on a model object with a ``chat`` method. The default is
``OpenAIModel`` which calls an OpenAI-compatible API. To plug in a different
backend, implement the ``Model`` protocol and pass an instance when creating the
agent.
