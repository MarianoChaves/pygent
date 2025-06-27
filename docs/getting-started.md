# Getting Started

This tutorial shows how to install Pygent and run a few basic commands. It also demonstrates how to use the Python API directly.

## Installation

Install from source in editable mode so the command line and Python modules are available:

```bash
pip install -e .[docker]
```

Docker is optional. If it is not available omit the `[docker]` extras and commands will run locally.

## Interactive session

Start the CLI by running `pygent`. Type normal instructions and each command will be executed in a sandboxed environment.

```bash
$ pygent --docker
vc> echo "Hello"
```

Use `/exit` to leave the session.

## Using the API

The `Agent` class exposes the same functionality programmatically. Here is a minimal example:

```python
from pygent import Agent

ag = Agent()
ag.step("echo 'Hello World'")
# additional steps...
ag.runtime.cleanup()
```

Check the `examples/` directory for more advanced scripts.
