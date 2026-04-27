# Multi-Agent Collaboration (Legacy)

> Legacy note: multi-agent orchestration is now optional and not the default product direction.

If you still need it, import directly from submodules:

```python
from pygent import Agent
from pygent.task_manager import TaskManager
from pygent.persona import Persona
```

Then you can start background tasks with `TaskManager.start_task(...)`, monitor status,
and collect files.

For most users, the recommended approach is the simpler single-agent CLI flow.
