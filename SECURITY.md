# Security policy

For a suspected vulnerability, use GitHub's private vulnerability reporting feature
on this repository if enabled. Otherwise contact the maintainer at
mchaves.software@gmail.com. Do not post credentials or sensitive exploitation details
in public issues.

The 2.0 release candidate includes execution-boundary fixes relative to 1.0. Read
[execution boundaries](docs/security.md) for the actual guarantees and limitations.
Local mode and the legacy HTTP server are intended for trusted use. There is no
claim of hostile multi-tenant sandboxing.
