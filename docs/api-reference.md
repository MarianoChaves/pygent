# API Reference

This section summarises the most relevant classes and functions.

## `Agent`

```python
from pygent import Agent
```

Manages the conversation with the model. Each instance owns a
`Runtime` accessible via ``agent.runtime``.

**Methods**

- `step(user_msg: str) -> None` – add a message and run any tools
  returned by the model.
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

Several tools are available by default:

- **bash** &ndash; executes shell commands via `Runtime.bash`.
- **write_file** &ndash; writes files through `Runtime.write_file`.
- **delegate_task** &ndash; start a background task handled by a new agent,
  optionally copying files into it.
- **task_status** &ndash; check the progress of a delegated task.
- **collect_file** &ndash; copy a file from a delegated task into the current workspace.
- **download_file** &ndash; retrieve the contents of a file from the workspace.

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

## `TaskManager`

Launch separate agents asynchronously and track them:

```python
from pygent import TaskManager, Runtime

rt = Runtime(use_docker=False)
tm = TaskManager()
task_id = tm.start_task(
    "generate report",
    rt,
    files=["data.txt"],
    step_timeout=5,
    task_timeout=60,
)
print(tm.status(task_id))
```
Pass a ``Runtime`` instance when starting a task so files can be copied into the
sub-agent workspace via the optional ``files`` argument. Delegated agents cannot
create further tasks. The maximum number of concurrent tasks is controlled by
the ``PYGENT_MAX_TASKS`` environment variable (default ``3``).
Optional ``step_timeout`` and ``task_timeout`` parameters control how long each
step and the overall task are allowed to run. Their defaults can be set via the
``PYGENT_STEP_TIMEOUT`` and ``PYGENT_TASK_TIMEOUT`` environment variables.

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

