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

See [Getting Started](getting-started.md) for installation instructions and the
[API Reference](api-reference.md) for details about the available classes.
