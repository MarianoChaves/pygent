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
  file in the working directory.
- `cleanup() -> None` – destroy the temporary workspace and stop the
  container if used.

## Tools

The agent can call two built-in tools:

- **bash** &ndash; executes shell commands via `Runtime.bash`.
- **write_file** &ndash; writes files through `Runtime.write_file`.

Refer to the `tools.py` module for the implementation details.
