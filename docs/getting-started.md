# Getting Started

Pygent is a simple agentic CLI for coding tasks.
It executes commands in Docker when available, and locally when Docker is not available.

## Installation

```bash
pip install pygent
```

If you want Docker SDK integration:

```bash
pip install pygent[docker]
```

From source:

```bash
pip install -e .
# optional
pip install -e .[docker]
```

## First interactive session

```bash
pygent
```

Useful startup options:

* `--docker` / `--no-docker`
* `--config path/to/pygent.toml`
* `--cwd` (use current directory as workspace)
* `--confirm-bash` / `--no-confirm-bash`
* `--ban-cmd CMD` (repeatable)
* `--load DIR` (resume snapshot)

Inside the session:

* `/help` and `/help <cmd>`
* `/cmd <command>`
* `/cp <source> [destination]`
* `/tools`, `/banned`, `/confirm-bash on|off`
* `/save <dir>` and `/exit`

## Programmatic usage

```python
from pygent import Agent

ag = Agent()
ag.step("echo 'Hello World'")
ag.runtime.cleanup()
```

## Next steps

* Configuration variables: [Configuration](configuration.md)
* Tool registry and custom tools: [Tools](tools.md)
* Custom model integration: [Custom Models](custom-models.md)
* Full API docs: [API Reference](api-reference.md)
