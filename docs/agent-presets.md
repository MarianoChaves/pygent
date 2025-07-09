# Agent Presets

The :mod:`pygent.agent_presets` module bundles ready-made configurations for common
workflows. Each preset combines a system message builder from the
:mod:`pygent.prompt_library` with a default set of tools.

Use :data:`~pygent.agent_presets.AGENT_PRESETS` to select one:

```python
from pygent import AGENT_PRESETS

ag = AGENT_PRESETS["autonomous"].create_agent()
ag.run_until_stop("echo hello")
```

The available presets and their behaviours are:

| Name | Tools | Description |
| --- | --- | --- |
| ``autonomous`` | ``bash``, ``write_file``, ``stop`` | Provides a complete professional solution, tests the result and summarises before finishing with ``stop``. |
| ``assistant`` | ``bash``, ``write_file``, ``ask_user`` | Interactive style that asks for clarifications and presents menu options when possible. |
| ``reviewer`` | ``bash`` | Focuses on analysing code and suggesting improvements. |

You can create your own preset by instantiating
:class:`~pygent.agent_presets.AgentPreset` with a custom builder and tool list.

To start an interactive session using a preset from the command line:

```bash
pygent --preset autonomous
```
