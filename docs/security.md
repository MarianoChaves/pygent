# Execution boundaries

Pygent runs model-selected actions. Treat tool availability as a capability grant.
For `Harness`, the default tool set is empty. Side-effecting tools can require an
application approval callback, and JSON Schema validation happens before execution.

## Docker and local mode

`Runtime()` requires Docker by default. Missing Docker or a failed container
startup is an error, never permission to execute on the host. Local execution is
explicit and has the current user's filesystem, network and environment access.
A workspace directory and shell command denylist are not security sandboxes.
Denylist checks are convenience filters and can be bypassed by shell composition.

Docker runtime containers disable networking and limit memory to 512 MB and process
count to 256. They mount the workspace writable. Containers run for the lifetime of
a runtime, not one container per shell command. Custom images must provide `sh`
and GNU `timeout`. Docker exec transport failures and pathological daemon behavior
need external supervision. The runtime does not promise isolation suitable for
hostile multi-tenant code; use hardened OS/VM boundaries for that threat model.

Local command timeouts kill process groups on POSIX. Programs that deliberately
escape the group/session are outside this guarantee. Windows descendant termination
has not been implemented as a Job Object and is not claimed. Captured command output
is bounded; custom tool implementations need their own memory/I/O controls.

## Files

Workspace methods reject absolute paths, traversal outside the root, and symlink
paths. Recursive copies reject nested symlinks. Upload sources and export destinations
are host paths explicitly selected by the application; do not expose those choices
as unrestricted model tools.

Path checks are not atomic filesystem confinement against a concurrently hostile
process. Symlink-swap races and pre-existing hard links require OS isolation. Do not
share a writable workspace with an untrusted process and rely on path validation
alone. Shell commands are not constrained by Python file-method checks in local mode.

## State and services

History writes use atomic replacement, but a history file is not a durable execution
journal. Do not share a history file among concurrent writers. Logs and transcripts
can contain secrets and personal information. Pygent does not redact them for you.
The legacy CLI can execute a trusted `config.py`; inspect repository configuration
before launching it.

The legacy FastAPI server has no authentication, tenant isolation, durable task
queue or retention policy. Keep it on loopback behind a trusted local application.
Do not expose it directly to the internet. The new harness does not start a server.

Report security issues using the instructions in the repository's `SECURITY.md`.
