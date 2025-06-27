# API Reference

This section summarises the most relevant classes and functions.

## `Agent`

```python
from pygent import Agent
```

The main entry point for interacting with Pygent. It keeps a conversation history and exposes a `step()` method to process user messages. Tool calls are automatically executed and their output appended to the history. Each `Agent` owns a `Runtime` instance stored in `agent.runtime`.

### `Agent.step(user_msg: str) -> None`
Adds the message to the conversation, queries the model and prints any tool output.

### `run_interactive(use_docker: bool | None = None) -> None`
Launches an interactive shell similar to the command line interface.

## `Runtime`

Handles command execution either in a Docker container or locally. Important methods include:

- `bash(cmd: str, timeout: int = 30) -> str` &ndash; run a shell command and return its combined output.
- `write_file(path: str, content: str) -> str` &ndash; create or replace a file inside the working directory.
- `cleanup() -> None` &ndash; destroy the temporary workspace and stop the container if used.

## Tools

The agent can call two built-in tools:

- **bash** &ndash; executes shell commands via `Runtime.bash`.
- **write_file** &ndash; writes files through `Runtime.write_file`.

Refer to the `tools.py` module for the implementation details.
