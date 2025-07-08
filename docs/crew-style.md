# Multi-Agent Collaboration

Pygent can coordinate multiple agents in parallel using the `TaskManager` class. This approach resembles systems like Crew AI where tasks are distributed to specialised agents.

## Defining personas

Create a list of `Persona` objects representing the roles of the agents that will form the "crew":

```python
from pygent import Agent, TaskManager
from pygent.persona import Persona

personas = [
    Persona("writer", "produces files"),
    Persona("reviewer", "checks the result"),
]

manager = TaskManager(personas=personas)
```

## Delegating tasks

Use `start_task` to launch background subtasks. Specify the desired persona and optionally send supporting files:

```python
main = Agent()

# Send a writer agent to generate a file
writing = manager.start_task(
    "write_file path='note.txt' content='hi'\nstop",
    main.runtime,
    persona="writer",
)

# Another agent reads the file and prints it to the console
reading = manager.start_task(
    "bash cmd='cat note.txt'\nstop",
    main.runtime,
    files=["note.txt"],
    persona="reviewer",
)
```

## Monitoring and collecting results

The `TaskManager` lets you check task status and copy files back to the main agent:

```python
import time
for tid in [writing, reading]:
    while manager.status(tid) == "running":
        time.sleep(1)
    print("Task status", tid + ":", manager.status(tid))

print(manager.collect_file(main.runtime, writing, "note.txt"))
main.runtime.cleanup()
```

With these calls you can build chained or parallel workflows, achieving behaviour similar to multi-agent frameworks like Crew AI.
