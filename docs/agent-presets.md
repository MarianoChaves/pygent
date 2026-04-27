# Agent Presets (Legacy)

> Legacy note: presets are no longer part of the default CLI architecture.

The old `pygent.agent_presets` module still exists for compatibility in some setups,
but the recommended approach is now to configure behavior directly with:

* `set_system_message_builder(...)`
* tool enable/disable controls

## Migration path

Instead of presets:

```python
from pygent import Agent, set_system_message_builder
from pygent.prompt_library import PROMPT_BUILDERS

set_system_message_builder(PROMPT_BUILDERS["autonomous"])
ag = Agent()
```

For CLI sessions, start plain `pygent` and adjust tools interactively (`/tools`).
