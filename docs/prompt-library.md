# Prompt Library

`pygent.prompt_library` provides ready-made system-message builders for common styles.

Use with `set_system_message_builder`:

```python
from pygent import Agent, set_system_message_builder
from pygent.prompt_library import PROMPT_BUILDERS

set_system_message_builder(PROMPT_BUILDERS["autonomous"])
ag = Agent()
ag.run_until_stop("echo hello")
```

Available builders:

| Name | Description |
| --- | --- |
| `autonomous` | Tries to execute tasks end-to-end with minimal user interaction. |
| `assistant` | Interactive style that asks for clarification when needed. |
| `reviewer` | Focused on code review and improvement suggestions. |

These builders are independent and can be combined with your own tool strategy.
