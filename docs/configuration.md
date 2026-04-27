# Configuration

Pygent reads settings from environment variables and optionally from `pygent.toml`.

## Core variables (recommended)

| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key for OpenAI or compatible provider. | – |
| `OPENAI_BASE_URL` | Base URL for OpenAI-compatible API. | `https://api.openai.com/v1` |
| `PYGENT_MODEL` | Model name used by the agent. | `gpt-4.1-mini` |
| `PYGENT_USE_DOCKER` | Set `0` to force local execution. | auto |
| `PYGENT_IMAGE` | Docker image for sandbox execution. | `python:3.12-slim` |
| `PYGENT_HISTORY_FILE` | Persisted conversation history file. | – |
| `PYGENT_WORKSPACE` | Persistent workspace directory. | – |
| `PYGENT_SNAPSHOT` | Snapshot directory to load on startup. | – |
| `PYGENT_LOG_FILE` | CLI log path. | `workspace/cli.log` |
| `PYGENT_CONFIRM_BASH` | Require bash confirmation (`0` disables). | `1` |
| `PYGENT_BANNED_COMMANDS` | Blocked commands (`os.pathsep` separated). | – |
| `PYGENT_BANNED_APPS` | Blocked apps (`os.pathsep` separated). | – |
| `PYGENT_INIT_FILES` | Files/dirs copied at startup (`os.pathsep` separated). | – |
| `PYGENT_PERSONA_NAME` | Main persona name. | `Pygent` |
| `PYGENT_PERSONA` | Main persona description. | `a sandboxed coding assistant.` |

## Optional legacy multi-agent variables

These only matter if you explicitly use `TaskManager` / `register_task_tools()`.

| Variable | Description | Default |
| --- | --- | --- |
| `PYGENT_MAX_TASKS` | Max concurrent delegated tasks. | `3` |
| `PYGENT_STEP_TIMEOUT` | Per-step timeout for delegated tasks. | – |
| `PYGENT_TASK_TIMEOUT` | Total timeout for delegated tasks. | – |
| `PYGENT_TASK_PERSONAS` | Delegated personas (`os.pathsep` separated). | – |
| `PYGENT_TASK_PERSONAS_JSON` | JSON array for delegated personas. | – |

## `pygent.toml`

You can define these keys in `pygent.toml`:

```toml
persona_name = "FriendlyBot"
persona = "a friendly bot"
initial_files = ["bootstrap.py"]
```

Then start with:

```bash
pygent --config path/to/pygent.toml
```

You can also pass env vars directly in CLI:

```bash
pygent -e OPENAI_API_KEY=sk-... -e PYGENT_MODEL=gpt-4
```
