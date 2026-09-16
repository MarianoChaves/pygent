# Changelog

## 2.0.0rc1

### Added

- `Harness`, `Tool`, `RunLimits`, `RunResult`, and metadata-only `RunEvent` callbacks.
- Explicit per-harness tools, JSON Schema argument/output validation, fail-closed
  tool approval, model-turn/tool-call budgets, cooperative cancellation/deadlines.
- `ScriptedModel` for deterministic offline tests and two executable quickstarts.
- Model client injection for explicit connection, timeout and retry configuration.
- Migration guide, execution boundaries, assessment, contribution and security docs.

### Fixed

- Docker startup failures can no longer silently enable host execution.
- Workspace file traversal and symlink escapes, including recursive copies and
  delegated task file collection.
- Disabled tools are blocked at dispatch; malformed bash arguments return errors.
- History preserves tool-call IDs on restoration and uses atomic file replacement.
- Docker shell composition and unsupported SDK `exec_run(timeout=...)` argument.
- POSIX local shell descendants on timeout and bounded command output capture.
- Concurrent task admission exceeding `max_tasks`.
- Process-global default log-file contamination across agents.
- Removed `imghdr` dependency, which prevented imports on Python 3.13+.
- Empty tool lists no longer send inappropriate automatic tool-choice parameters.

### Compatibility and limits

Python 3.10+ is required. Local execution must be explicit; workspace paths must be
relative and cannot traverse symlinks. Runtime command capture is bounded by default.
See the migration guide. Distributed execution, MCP, native async/model streaming,
token accounting and durable side-effect recovery are not part of this candidate.
