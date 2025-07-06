# Tools

Tools are at the heart of Pygent's functionality, allowing the agent to interact with the file system, execute commands, and perform other actions.

## Native Tools

Pygent comes with a set of essential tools ready to use:

* **`bash`**: Executes a shell command in the execution environment (local or Docker).
    * **Parameters**: `cmd` (string) - The command to be executed.
* **`write_file`**: Creates or overwrites a file in the agent's workspace.
    * **Parameters**: `path` (string), `content` (string).
* **`stop`**: Stops the agent's autonomous execution loop. Useful for signaling the end of a task.
* **`ask_user`**: Used to request a response or input from the user, continuing the conversation.

## Task Tools

To manage subtasks and background agents, Pygent offers specific tools that are activated by registering with `register_task_tools()`:

* **`delegate_task`**: Creates a new background task with a new agent.
    * **Parameters**: `prompt` (string), `files` (list of strings, optional), `persona` (string, optional), `timeout` (float, optional).
* **`task_status`**: Checks the status of a delegated task.
    * **Parameters**: `task_id` (string).
* **`collect_file`**: Retrieves a file or directory from a delegated task to the main agent's workspace.
    * **Parameters**: `task_id` (string), `path` (string), `dest` (string, optional).
* **`list_personas`**: Returns the available personas for delegated tasks.

## Creating Custom Tools

You can easily extend Pygent with your own tools.

### Using `register_tool`

The most direct way to register a new tool is using the `register_tool` function.

```python
from pygent import Agent, register_tool

# The tool function always receives the runtime as the first argument
def hello(rt, name: str) -> str:
    return f"Hello {name}!"

# Register the tool
register_tool(
    "hello", # Tool name
    "Greet by name", # Description
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, # Parameter schema
    hello # The function to be called
)

ag = Agent()
# Now the agent can use the 'hello' tool
ag.step("hello name='world'")
ag.runtime.cleanup()
```

### Using the `@tool` decorator
Alternatively, you can use the `@tool` decorator for a more concise registration:

```python
from pygent import tool, Agent

@tool(
    name="goodbye",
    description="Say goodbye",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
)
def goodbye(rt, name: str) -> str:
    return f"Goodbye {name}!"

ag = Agent()
ag.step("goodbye name='world'")
ag.runtime.cleanup()
```