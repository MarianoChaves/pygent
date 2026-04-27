# Tools

Tools are how the model performs actions in the workspace.

## Built-in core tools

These are enabled by default:

* **`bash`**: run a shell command.
  * params: `cmd: string`
* **`write_file`**: create/overwrite files in workspace.
  * params: `path: string`, `content: string`
* **`read_image`**: read an image file and return a data URL.
  * params: `path: string`
* **`ask_user`**: request additional user input.
* **`stop`**: signal the autonomous loop to stop.

## Optional legacy task tools

If you want delegated multi-agent flows, register them explicitly:

```python
from pygent.task_tools import register_task_tools

register_task_tools()
```

Additional tools then become available:

* `delegate_task`
* `delegate_persona_task`
* `task_status`
* `collect_file`
* `list_personas`
* `download_file`

## Registering custom tools

```python
from pygent import Agent, register_tool

def hello(rt, name: str) -> str:
    return f"Hello {name}!"

register_tool(
    "hello",
    "Greet by name",
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    hello,
)

ag = Agent()
ag.step("hello name='world'")
```

Decorator version:

```python
from pygent import Agent, tool

@tool(
    name="goodbye",
    description="Say goodbye",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
)
def goodbye(rt, name: str) -> str:
    return f"Goodbye {name}!"
```
