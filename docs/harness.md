# Harness API

`Harness` wraps a `Model` and an explicit collection of `Tool` objects. Unlike the
legacy `Agent`, it does not print to the terminal, read CLI configuration, create a
runtime, or consult the global tool registry. Tool functions receive keyword
arguments validated against their JSON Schema.

## Run lifecycle

1. Copy the supplied history, or create a system message, then add the prompt.
2. Check cancellation/deadline and call the model with the available tool schemas.
3. If the model returns a final answer, validate `output_schema` when supplied.
4. Otherwise, check the entire tool batch against the remaining budget.
5. Validate each call, check approval when required, execute, and append its result.
6. Continue until completion or a limit; return a `RunResult`.

Tool call IDs must be nonempty and unique within a response. Each accepted model
batch receives one tool response per call, including calls skipped for limits or
cancellation. A tool failure becomes an error response that the model can act on.
Malformed model messages, provider errors, approval errors and event-sink errors
propagate to the caller. No external action is retried automatically.

## Tools and approval

```python
from pygent import Tool

lookup = Tool(
    "lookup", "Look up an internal package by name.",
    {"type": "object", "properties": {"name": {"type": "string"}},
     "required": ["name"], "additionalProperties": False},
    function=lambda name: {"name": name, "supported": True},
)
```

Mark mutations with `requires_approval=True`. They are denied unless
`run(approve=callback)` returns exactly `True`. The callback gets `(tool_name,
arguments)` with an independent copy of the validated arguments. The application
owns the approval UI and policy. This callback does not implement persisted
human-in-the-loop suspension; do not block a web request waiting for approval.

Each harness snapshots its tool metadata at construction. Registries are independent.
Functions themselves are not copied and must be safe for the intended concurrency.
Unknown tools never dispatch to the legacy registry. JSON Schema `default` values
are annotations, not automatically inserted values. Tool functions must return text
or JSON-serializable values; non-finite JSON values are rejected.

## Limits and status

| Status | Meaning |
| --- | --- |
| `completed` | Model produced a final answer; optional output schema passed |
| `max_steps` | Model-turn budget exhausted |
| `max_tool_calls` | Next batch would exceed tool-call budget; batch skipped |
| `timeout` | Cooperative deadline observed between calls |
| `cancelled` | Cancellation event observed between calls |
| `invalid_output` | Final answer was not JSON conforming to the output schema |

`RunLimits()` defaults to 20 model calls, 100 tool attempts, and 16,000 characters
per tool result. `max_time=None` means no harness deadline. Denied, unknown and
invalid calls consume tool attempts. Budget-skipped calls do not. The truncation
marker is additional to the retained-character budget. This is a context capture
limit, not a limit on memory allocated inside an arbitrary tool function.

Cancellation uses `threading.Event`. Deadlines/cancellation do not preempt Python
functions, pending approvals, event callbacks or model calls. Configure provider
and tool I/O timeouts. `Runtime.bash` has a separate command timeout and bounded
capture, including output with no newline. Arbitrary custom tools need their own
resource limits.

## Structured answers and telemetry

```python
schema = {"type": "object", "properties": {"passed": {"type": "boolean"}},
          "required": ["passed"], "additionalProperties": False}
# Ask for JSON explicitly in your prompt. This validates locally; it does not
# enable a provider-specific constrained decoding mode.
result = harness.run("Return JSON with a boolean passed field.", output_schema=schema)
if result.status == "completed":
    print(result.data["passed"])
```

Pass `on_event=callback` to route `RunEvent` values into your own logs or traces.
Events include run ID, step, elapsed time, tool name/call ID and outcome. They do
not include prompts, arguments or outputs. Tool names and IDs can still contain
application-specific information. Events are also stored in the result.

`result.to_dict()` is JSON-serializable. Its messages and output may contain
sensitive data; choose redaction, access control and retention at the application
boundary. Pygent does not upload telemetry.

## Continuation and orchestration

Continue with `harness.run(next_prompt, history=result.messages)`. Each run copies
its transcript and has independent counters. Supply only trusted, complete
transcripts. A new run resets its budget. A model re-requesting a tool can repeat
its side effect; use application idempotency keys where necessary.

Saving a result is not a durable checkpoint: a crash between a side effect and
saving its result can leave uncertain execution state. Use a workflow engine and
idempotent tools when recovery is required. To use Pygent inside an existing
orchestrator, invoke `run` as an ordinary synchronous function and persist the
returned status and transcript. Native LangGraph/MCP adapters are not included.

For concurrent jobs, use separate model/tool instances or explicitly thread-safe
implementations. `ScriptedModel` is deliberately sequential. Native asyncio and
streaming model responses are future work.
