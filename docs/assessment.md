# Technical assessment and roadmap

Review baseline: `f8eca69857be295a5a214608bfc4e23ce7865155` (main).
Assessment date: 2026-09-16. This is a source review with deterministic regression
tests, not a penetration test, load benchmark or model-quality evaluation.

## Findings

| Finding in the baseline | Consequence | Candidate response |
| --- | --- | --- |
| Docker failure silently changes execution mode | Model-generated commands can reach the host unexpectedly | Fail closed; local execution explicit |
| File methods join untrusted paths to the workspace | Absolute paths, traversal and symlinks can cross the intended boundary | Workspace-relative validation and recursive-copy symlink checks |
| Disabled tools filtered only from schemas | A model can still invoke a disabled tool | Enforce denial at dispatch |
| History restore converts every dictionary to `Message` | Tool response IDs disappear; system-message refresh can fail | Preserve role-specific dictionaries and tool-call IDs |
| History rewritten directly to destination | Interrupted writes can leave truncated JSON | Atomic replacement |
| Docker exec receives unsupported `timeout` keyword | Normal non-streaming execution returns an error | GNU timeout inside a shell command, streaming capture |
| Local timeout kills only shell; waits on inherited pipe | Child processes may survive and delay return | POSIX group termination with bounded reader wait |
| Tool/command output accumulated without a bound | Large output can exhaust memory/context | Runtime capture and harness response limits |
| Global registry and default log environment mutation | Independent applications/agents can affect each other | Explicit harness registry; per-agent default logging |
| Task admission check and insertion separated by lock release | Concurrent callers can exceed maximum tasks | Atomic admission through registration |
| `imghdr` imported at module import time | Python 3.13+ cannot import package | Small supported image-signature checks |
| Tests inject global third-party stubs | SDK/display behavior can be hidden | Load installed dependencies; explicit offline model doubles |

These changes do not turn a directory into an OS sandbox. Concurrent filesystem
mutation, hard links, hostile shell code and Docker daemon faults require separate
isolation/supervision. The legacy server still lacks authentication and durable
storage; it remains a trusted-local interface.

## Fit with today's harness ecosystem

[LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) addresses
orchestration, streaming, human intervention and durable execution. Its
[persistence layer](https://docs.langchain.com/oss/python/langgraph/persistence)
records checkpoints for recovery and continuation. Pygent should integrate as a
small bounded function when those capabilities are already owned by the host
application; it should not claim equivalent durability from saved JSON history.

[Pydantic AI's agent documentation](https://pydantic.dev/docs/ai/core-concepts/agent/)
describes request, token, tool-call and cost limits. This candidate adopts the
useful principle of explicit execution budgets, but only implements model-turn,
tool-attempt, output-character and cooperative-time limits. It does not claim token
or cost accounting. Its JSON output validation is local validation, not guaranteed
provider-constrained generation.

The intended niche is therefore a **small, inspectable Python execution loop**:
ordinary functions, explicit capabilities, portable chat-model protocol, a result
that a caller can inspect, and tests that run without model access. This is an
engineering/product hypothesis, not evidence of community demand.

## Candidate scope

- Usable offline quickstart that executes a tool and verifies the transcript.
- Per-instance tools and approval decisions, schema validation, explicit bounds.
- Metadata-only event hooks for application-owned telemetry.
- Final-answer completion and separate incomplete-result statuses.
- Compatibility-preserving legacy `Agent` API where practical, with documented
  breaking execution-boundary changes in the 2.x candidate.
- Source build, docs build, package-content checks and Python-version CI matrix.

## Next work, prioritized by developer value

1. **Real integration evidence:** trial the harness in two developer workflows,
   such as repository checks and a read-only internal metadata assistant. Measure
   setup time, code needed, failure diagnosis, completion rate and cost per task.
2. **Provider usage and async contracts:** typed usage accounting, async model/tool
   protocols, cancellation propagation and streaming with backpressure. Add real
   provider contract tests gated by credentials, alongside offline tests.
3. **MCP adapters:** optional dependencies with explicit tool allowlists,
   lifecycle/timeout handling and approval propagation. Validate against supported
   protocol versions before advertising compatibility.
4. **Recovery through existing systems:** examples using a host workflow engine,
   idempotency keys and external checkpoint storage. State guarantees precisely;
   no exactly-once claims from a transcript file.
5. **Legacy server redesign:** authentication, tenant-owned workspaces, admission
   queues, lifecycle cleanup, retention and durable task state before public use.

Acceptance should depend on measured developer utility. A release or test count
cannot establish community success, distributed scalability or model effectiveness.
For model-quality evaluation, hold tasks/models/budgets constant, report sample
size and uncertainty, and compare task success and resource usage to a direct
model/tool-loop baseline.
