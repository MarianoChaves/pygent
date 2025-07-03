# Getting Started

Pygent is a minimalist coding assistant that runs shell commands inside a
sandboxed environment. By default a Docker container is used, but if Docker
is unavailable the commands run locally instead. This page shows how to install
the package and gives a few examples covering the main features.

## Installation

Install from source in editable mode so the CLI and Python modules are
available. Include the optional extras to enable Docker support and the web UI:

```bash
pip install pygent[docker,ui]
```

Python 3.9 or newer is required. If Docker is not installed omit the
`[docker]` extras and commands will run on the host system.

## Interactive session

Start an interactive session by running `pygent` in a terminal. Use the
`--docker` flag to force container execution or `--no-docker` to run locally.
The CLI prints the persona name and whether commands run `local` or in
`Docker` when the session starts so you know which agent is active.

```bash
$ pygent --docker
vc> echo "Hello"
```

Each message is executed in the sandbox and the output printed. Use `/exit`
to leave the session. You can also launch a simple web interface with
`pygent-ui` (requires the `ui` extra).

Use `/help` inside the CLI to list available commands. The helper shows
`/cmd` to run a raw shell command, `/cp` to copy files into the workspace
and `/new` to restart the conversation while keeping the current runtime.

### Tool usage

During the conversation the assistant can call several built-in tools. `bash`
runs shell commands and `write_file` creates files inside the workspace. For
example:

```text
vc> write_file path="hello.txt" content="Hello from Pygent"
vc> bash cmd="cat hello.txt"
```

You can disable all built-in tools with `pygent.clear_tools()` or
remove a specific one with `pygent.remove_tool("bash")`. Restore the
defaults at any time using `pygent.reset_tools()`. The system prompt will
update automatically to list the tools currently registered.

## Using the API

The same functionality is accessible programmatically via the `Agent` class:

```python
from pygent import Agent

ag = Agent()
ag.step("echo 'Hello World'")
ag.runtime.cleanup()
```

See [api_example.py](https://github.com/marianochaves/pygent/blob/main/examples/api_example.py)
for a complete script. Additional examples show how to implement a custom model
and how to interact with the `Runtime` class directly.

## Configuration

Pygent communicates with the model through an OpenAI‑compatible API. Export your
API key before running the assistant. A full list of environment variables is
available in the [Configuration](configuration.md) page.

For full control you may pass a custom model implementation to `Agent`. The file
[custom_model.py](https://github.com/marianochaves/pygent/blob/main/examples/custom_model.py)
contains a minimal echo model example. A dedicated [Custom Models](custom-models.md)
page expands on this topic with additional scenarios.

## Additional examples

Several scripts in the `examples/` directory showcase different parts of the
package (see the dedicated [Examples](examples.md) page):

- **api_example.py** &ndash; minimal use of the :class:`~pygent.agent.Agent` API.
- **runtime_example.py** &ndash; running commands through the
  :class:`~pygent.runtime.Runtime` class directly.
- **write_file_demo.py** &ndash; calling the built-in tools from Python code.
- **custom_model.py** &ndash; plugging in a custom model.

Below is the custom model snippet for reference:

```python
from pygent import Agent, openai_compat

class EchoModel:
    def chat(self, messages, model, tools):
        last = messages[-1]["content"]
        return openai_compat.Message(role="assistant", content=f"Echo: {last}")

ag = Agent(model=EchoModel())
ag.step("test")
ag.runtime.cleanup()
```

Custom models can also issue tool calls. The following model runs the last user
message as a `bash` command:

```python
import json
from pygent import Agent, openai_compat


class BashModel:
    def chat(self, messages, model, tools):
        cmd = messages[-1]["content"]
        call = openai_compat.ToolCall(
            id="1",
            type="function",
            function=openai_compat.ToolCallFunction(
                name="bash",
                arguments=json.dumps({"cmd": cmd}),
            ),
        )
        return openai_compat.Message(role="assistant", content=None, tool_calls=[call])


ag = Agent(model=BashModel())
ag.step("echo hi")
ag.runtime.cleanup()
```

See the [API reference](api-reference.md) for the complete list of classes and
configuration options.
