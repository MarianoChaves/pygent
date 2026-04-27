# Architecture

Pygent now prioritizes a **simple single-agent architecture**.

## Core components

* **`Agent`**: orchestrates messages, model calls, and tool execution.
* **`Runtime`**: executes commands and file operations in local or Docker workspace.
* **`Model`** (`OpenAIModel` by default): abstraction for OpenAI-compatible chat backends.
* **`tools` registry**: global registry used to expose callable actions to the model.

## Default request flow

1. User message enters `Agent`.
2. Agent updates history and sends context + tool schemas to model.
3. Model returns text and/or tool calls.
4. Agent executes tool calls through `Runtime`.
5. Results are appended to history and displayed.

## Optional legacy layer

A separate legacy layer still exists for delegated background tasks:

* `pygent.task_manager.TaskManager`
* `pygent.task_tools.register_task_tools()`

This layer is opt-in and not part of the default CLI flow.
