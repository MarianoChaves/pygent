# Prompt Library

This page collects a few ready-made system message builders that you can use
to quickly customise the agent's behaviour. They live in the
:mod:`pygent.prompt_library` module and work with
:func:`~pygent.agent.set_system_message_builder`. The
:mod:`pygent.agent_presets` module builds on top of these to offer ready-made
agents with preset tool sets.

```python
from pygent import Agent, set_system_message_builder, PROMPT_BUILDERS

# pick one of the predefined builders
set_system_message_builder(PROMPT_BUILDERS["autonomous"])

ag = Agent()
ag.run_until_stop("echo hello")
```

Available builders:

| Name | Description |
| --- | --- |
| ``autonomous`` | Operates autonomously in a computing environment without further user interaction. It inspects the environment first, performs the task step by step, tests the outcome and finishes with a final artefact or summary via ``stop``. |
| ``assistant`` | Encourages interactive behaviour asking for clarifications. |
| ``reviewer`` | Focuses on reviewing code and suggesting improvements. |

These builders are also used by the presets in
:mod:`pygent.agent_presets` which include sensible tool selections.
