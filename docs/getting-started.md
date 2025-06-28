# Getting Started

Pygent is a minimalist coding assistant that runs shell commands inside a
sandboxed environment. By default a Docker container is used, but if Docker
is unavailable the commands run locally instead. This page shows how to install
the package and gives a few examples covering the main features.

## Installation

Install from source in editable mode so the CLI and Python modules are
available. Include the optional extras to enable Docker support and the web UI:

```bash
pip install pygent[llm,docker,ui]
```

Python 3.9 or newer is required. If Docker is not installed omit the
`[docker]` extras and commands will run on the host system.

## Interactive session

Start an interactive session by running `pygent` in a terminal. Use the
`--docker` flag to force container execution or `--no-docker` to run locally.

```bash
$ pygent --docker
vc> echo "Hello"
```

Each message is executed in the sandbox and the output printed. Use `/exit`
to leave the session. You can also launch a simple web interface with
`pygent-ui` (requires the `ui` extra).

### Tool usage

During the conversation the assistant can call two built-in tools: `bash` to
run shell commands and `write_file` to create files inside the workspace. For
example:

```text
vc> write_file path="hello.txt" content="Hello from Pygent"
vc> bash cmd="cat hello.txt"
```

## Using the API

The same functionality is accessible programmatically via the `Agent` class:

```python
from pygent import Agent

ag = Agent()
ag.step("echo 'Hello World'")
ag.runtime.cleanup()
```

See `examples/api_example.py` for a complete script. Additional examples show
how to implement a custom model and how to interact with the `Runtime` class
directly.

## Configuration

Pygent talks to the language model through an OpenAI‑compatible API. Set your
credentials as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"  # change if using another provider
```

The model can be changed with `PYGENT_MODEL` and the Docker image with
`PYGENT_IMAGE`. Set `PYGENT_USE_DOCKER=0` to always disable containers.

For full control you may pass a custom model implementation to `Agent`. The
file `examples/custom_model.py` contains a minimal echo model example.

## Additional examples

Several scripts in the `examples/` directory showcase different parts of the
package:

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

See the [API reference](api-reference.md) for the complete list of classes and
configuration options.
