# Pygent

**A small Python harness for tool-using AI agents.** Bring a chat model and ordinary
Python functions; Pygent runs the loop with explicit tools, validation, approvals,
execution budgets and a serializable result.

Pygent is useful when you already have application logic and need a bounded agent
loop around it: repository maintenance, internal developer tools, or an agent step
inside a larger workflow. No graph DSL, database or automatic shell access is
required. The existing coding CLI remains available.

**2.0.0rc1 is a release candidate.** Python 3.10+; MIT licensed.
Read the [migration guide](docs/migration-v2.md) before upgrading from 1.x.

## Try it without an API key

Install this candidate from its source checkout:

```bash
python -m pip install -e .
python examples/offline_harness.py
```

```python
from pygent import Harness, RunLimits, Tool
from pygent.testing import ScriptedModel

model = ScriptedModel([
    {"role": "assistant", "tool_calls": [{
        "id": "check-1", "type": "function",
        "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
    }]},
    {"role": "assistant", "content": "The result is 5."},
])

add = Tool(
    name="add",
    description="Add two integers.",
    parameters={
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
        "additionalProperties": False,
    },
    function=lambda a, b: a + b,
)

harness = Harness(model, model_name="offline", tools=[add])
result = harness.run("What is 2 + 3?", limits=RunLimits(max_steps=3))
assert result.status == "completed"
print(result.output)  # The result is 5.
```

`ScriptedModel` is a deterministic test double, not a simulated quality benchmark.
It records requests so you can assert tool arguments and conversation protocol.

## Connect your model

The `Model` protocol consists of one method: `chat(messages, model, tools)`.
Return an assistant message containing text or function tool calls.
For an OpenAI-compatible Chat Completions endpoint:

```python
import os
from openai import OpenAI
from pygent import Harness, OpenAIModel

client = OpenAI(timeout=30.0, max_retries=0)  # OPENAI_API_KEY; optional OPENAI_BASE_URL
harness = Harness(OpenAIModel(client=client), model_name=os.environ["PYGENT_MODEL"])
result = harness.run("Explain this test failure: ...")
print(result.status, result.output)
```

Provider retries are configured on the client. Pygent never automatically retries
a tool with side effects. This adapter targets Chat Completions, not every vendor's
native API. See [custom models](docs/custom-models.md).

## Explicit control, inspectable results

| Need | API / behavior |
| --- | --- |
| Limit model turns and tool attempts | `RunLimits(max_steps=20, max_tool_calls=100)` |
| Bound each tool response in context | `RunLimits(max_output_chars=16_000)` |
| Cooperative deadline or cancellation | `max_time` and `run(cancel=threading.Event())` |
| Require application approval | `Tool(..., requires_approval=True)` and `run(approve=...)` |
| Validate inputs before side effects | JSON Schema per tool, including nested types |
| Validate a JSON final answer | `run(output_schema=...)`; inspect `result.data` |
| Integrate tracing | `run(on_event=...)`; events exclude prompt/argument/output content |
| Continue a completed turn | `run(..., history=result.messages)` |
| Evaluate without network | `ScriptedModel` and ordinary `pytest` assertions |

A final answer ends the loop. Exhausting a budget is a distinct result status,
never reported as completion. Tool batches exceeding the remaining tool budget
are rejected before any call in that batch executes. See the
[harness guide](docs/harness.md) for detailed semantics and examples.

## Files and commands: opt in

`Harness` starts with **zero tools** and creates no workspace. Bind `Runtime`
methods explicitly when an application needs file or shell access. The
[workspace example](examples/workspace_harness.py) shows a write tool with approval.

For the interactive coding CLI:

```bash
python -m pip install -e '.[docker]'
pygent --docker
```

Docker must be installed and running. Failure to start Docker raises an error.
Trusted local execution must be selected explicitly:

```bash
pygent --no-docker
```

Local shell commands have the invoking user's permissions. A working directory
and command denylist do not create a sandbox. Docker limits network access,
memory and process count, but the mounted workspace remains writable. Read the
[execution boundaries](docs/security.md) before enabling shell tools.

## Scope and limits

This candidate provides a synchronous, in-process harness. Use independent model
and tool instances per concurrent worker unless they are thread-safe. Deadlines
and cancellation are checked **between calls**; configure I/O timeouts on models
and tools. POSIX shell process groups and Docker's `timeout` bound runtime commands.

There is no native MCP client/server, durable workflow engine, distributed queue,
token/cost accounting, native async streaming, or exactly-once side-effect guarantee.
Use an existing orchestrator for those requirements. The
[technical assessment and roadmap](docs/assessment.md) explain the intended niche
and the remaining work. The legacy HTTP server is not a public multi-tenant service.

## Develop and contribute

```bash
python -m pip install -e '.[test,docs,dev]'
python -m pytest -q
python -m ruff check pygent tests
python -m mkdocs build --strict
python -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md),
[API reference](docs/api-reference.md) and [LICENSE](LICENSE).
