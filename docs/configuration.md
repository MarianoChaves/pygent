# Configuration

This page summarises the environment variables that control Pygent.  They can be
exported in your shell or set via a `.env` file before running the CLI.

| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key for OpenAI or any compatible service. | – |
| `OPENAI_BASE_URL` | Base URL for the API endpoint. | `https://api.openai.com/v1` |
| `PYGENT_MODEL` | Model name used for requests. | `gpt-4.1-mini` |
| `PYGENT_IMAGE` | Docker image used for sandboxed execution. | `python:3.12-slim` |
| `PYGENT_USE_DOCKER` | Set to `0` to run commands locally. Otherwise the runtime will try to use Docker if available. | auto |
| `PYGENT_MAX_TASKS` | Maximum number of delegated tasks that can run concurrently. | `3` |
| `PYGENT_STEP_TIMEOUT` | Default time limit in seconds for each step when running delegated tasks. | – |
| `PYGENT_TASK_TIMEOUT` | Default overall time limit in seconds for delegated tasks. | – |
| `PYGENT_PERSONA` | System prompt preamble for the main agent. | "You are Pygent, a sandboxed coding assistant." |
| `PYGENT_TASK_PERSONAS` | List of personas for delegated agents separated by `os.pathsep`. | – |
| `PYGENT_INIT_FILES` | List of files or directories copied into the workspace at startup, separated by `os.pathsep`. | – |

Instead of setting environment variables you can create a `pygent.toml` file in
the current directory or in your home folder. Values defined there are loaded at
startup if the corresponding variables are unset. Example:

```toml
persona = "You are a friendly bot"
task_personas = ["tester", "developer"]
initial_files = ["bootstrap.py"]
```

The keys map to the environment variables of the same name.

You can also specify a configuration file explicitly when launching the CLI:

```bash
pygent --config path/to/pygent.toml
```

A practical example is included in
[`examples/sample_config.toml`](https://github.com/marianochaves/pygent/blob/main/examples/sample_config.toml)
together with the script
[`config_file_example.py`](https://github.com/marianochaves/pygent/blob/main/examples/config_file_example.py), which delegates a testing task:

```bash
python examples/config_file_example.py
```


See [Getting Started](getting-started.md) for installation instructions and the
[API Reference](api-reference.md) for details about the available classes.
