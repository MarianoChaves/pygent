# API Reference

This page describes the public classes and helpers provided by **Pygent**. Import everything from the package root unless noted otherwise.

## `Agent`

```python
from pygent import Agent
```

`Agent` orchestrates the conversation with the selected model. Each instance owns a `Runtime` available as `agent.runtime`.

### Methods

- `step(user_msg: str) -> pygent.openai_compat.Message` – add a message and run any tools returned by the model.
- `run_interactive(use_docker: bool | None = None) -> None` – start a terminal session.
- `run_gui(use_docker: bool | None = None) -> None` – launch the simple web interface.
- `run_until_stop(user_msg: str, max_steps=20, ...) -> None` – keep executing steps until the `stop` tool is called or a limit is reached.

## `Runtime`

`Runtime` executes commands either locally or in a Docker container.

### Methods

- `bash(cmd: str, timeout: int = 30) -> str` – run a shell command and return its output.
- `write_file(path: str, content: str) -> str` – create or overwrite a UTF‑8 file.
- `read_file(path: str, binary: bool = False) -> str` – read a file from the workspace.
- `cleanup() -> None` – destroy the temporary workspace and stop the container if one was used.

## Built‑in tools

These tools are registered automatically:

- **bash** – run a command through `Runtime.bash`.
- **write_file** – create files via `Runtime.write_file`.
- **delegate_task** – start a background agent.
- **delegate_persona_task** – like `delegate_task` but lets you pick the persona.
- **list_personas** – return the available personas for delegation.
- **task_status** – check the status of a delegated task.
- **collect_file** – copy a file from a delegated task into the current workspace.
- **download_file** – read a file using `Runtime.read_file`.
- **continue** – request user input when running autonomously.
- **stop** – stop the autonomous loop.

Custom tools can be registered programmatically:

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

## `TaskManager`

```python
from pygent import TaskManager, Runtime
```

`TaskManager` launches separate agents asynchronously and tracks them. Pass a `Runtime` instance when starting a task so files can be copied into the sub‑agent's workspace.

## Personas

Agents can adopt different personas. The defaults come from the `PYGENT_PERSONA_NAME` and `PYGENT_PERSONA` environment variables. Delegated agent personas can be configured via `PYGENT_TASK_PERSONAS_JSON`. The `list_personas` tool returns all available options.

## Custom prompts

Provide a `Persona` object to the `Agent` constructor to override the system prompt:

```python
from pygent import Agent, Persona

ag = Agent(persona=Persona("Helper", "a friendly bot"))
```

## Custom models

`Agent` relies on an object implementing the `Model` protocol. The default `OpenAIModel` calls an OpenAI‑compatible API, but any backend can be plugged in. Custom models may return tool calls by filling the `tool_calls` attribute of the returned message.
