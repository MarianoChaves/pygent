# Architecture

Understanding Pygent's architecture helps in effectively customizing and extending the project. The system is composed of a few main components that work together.

## Core Components

* **`Agent`**: The `Agent` is the central orchestrator. It maintains the conversation history, interacts with the language model to decide the next step, and dispatches calls to tools. Each agent has its own state, including its persona and enabled tools.

* **`Runtime`**: The `Runtime` represents the isolated execution environment. It is responsible for executing commands (`bash`), interacting with the file system (`write_file`, `read_file`), and managing the environment's lifecycle (e.g., a Docker container). If Docker is unavailable, the `runtime` executes commands locally. Each agent has its own `runtime` instance, ensuring isolation between tasks.

* **`Model`**: The `Model` is an interface (protocol) that abstracts communication with a language model (LLM). The default implementation, `OpenAIModel`, interacts with OpenAI-compatible APIs. You can provide your own implementation to connect to different model backends.

* **`TaskManager`**: The `TaskManager` manages the execution of background tasks. When you use the `delegate_task` tool, the `TaskManager` creates a new `Agent` with its own `Runtime` to execute the task asynchronously. This allows the main agent to continue its work or monitor the subtask's progress.

## Request Flow

1.  The user sends a message to the `Agent` via the CLI or API.
2.  The `Agent` adds the user's message to the conversation history.
3.  The `Agent` sends the complete history to the `Model`.
4.  The `Model` returns a response, which can be a text message or a request to call one or more tools (`tool_calls`).
5.  If it's a text message, the `Agent` displays it to the user.
6.  If it's a tool call, the `Agent` invokes the corresponding function (e.g., `tools._bash`), passing the necessary arguments to the `Runtime`.
7.  The `Runtime` executes the action (e.g., an `ls` command in the Docker container).
8.  The result of the execution is returned to the `Agent`.
9.  The `Agent` adds the tool's result to the history and typically calls the `Model` again so it can process the result and decide the next step, continuing the cycle until the task is completed (signaled by the `stop` tool).