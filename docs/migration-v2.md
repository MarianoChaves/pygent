# Migrating from 1.x to 2.0.0rc1

This release candidate changes execution boundaries. Test your integration before
upgrading production workloads.

| 1.x behavior | 2.x behavior / action |
| --- | --- |
| Docker errors silently select local execution | Docker errors raise; use `Runtime(use_docker=False)`, `--no-docker`, or `PYGENT_USE_DOCKER=0` only for trusted local use |
| Python 3.9 advertised | Python 3.10+ supported; newer Python no longer depends on removed `imghdr` |
| Workspace methods accept absolute/escaping paths | Supply workspace-relative paths; symlinks in file/copy paths are rejected |
| A disabled tool is only hidden from the model | `Agent` now blocks it at dispatch too |
| Unbounded command output capture | `Runtime.bash` retains up to 64,000 characters by default; `max_output_chars` configures it |
| Local timeout kills only the shell | On POSIX, the process group is killed; background children do not survive ordinary command completion |
| First agent sets a process-wide log-file default | Each agent selects its own log path; explicit `PYGENT_LOG_FILE` still applies |
| History rewrites can leave partial JSON; restored tool IDs are lost | Atomic replacement and preserved tool-call IDs; interrupted/incomplete turns are not automatically recovered |

`Agent.step`, its mixed legacy history representation, `run_until_stop`, and CLI
commands remain available. `Harness` is the recommended API for new integrations:
its tools are explicit, it has no interactive terminal behavior, and it returns
`RunResult` with a termination reason.

`Harness` does not reuse global `register_tool` entries. Construct `Tool` objects
explicitly. Tool functions take validated keyword arguments, with no automatically
injected `Runtime` parameter; use bound runtime methods or closures.

The legacy autonomous loop still has its older stop-tool semantics and cooperative
post-step timeout checks. Do not confuse it with the new harness's final-answer
termination and per-batch budgeting.
