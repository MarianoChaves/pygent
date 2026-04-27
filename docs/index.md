# Welcome to Pygent

**Pygent** is a minimalist coding assistant focused on one core workflow:
**an agentic CLI that can safely execute commands in an isolated workspace**.

By default, Pygent tries to run commands in Docker. If Docker is unavailable,
it falls back to local execution.

## Highlights

* **Simple default flow**: single-agent interactive CLI.
* **Safe execution model**: isolated workspace and optional Docker runtime.
* **OpenAI-compatible**: works with OpenAI and compatible providers.
* **Extensible**: register custom tools and plug custom models.
* **Stateful sessions**: history, snapshots, and reusable workspaces.

## Start here

* New user? Read **[Getting Started](getting-started.md)**.
* CLI details? Go to **[CLI](cli.md)**.
* Want customization? See **[Tools](tools.md)** and **[Custom Models](custom-models.md)**.
* Want internals? Read **[Architecture](architecture.md)**.

## About legacy advanced features

Older multi-agent/preset/server flows are still documented in **Optional Legacy Features**.
They are no longer the default product direction.
