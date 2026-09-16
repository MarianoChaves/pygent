# Pygent

A small Python harness for tool-using AI agents: explicit tools, validation,
approvals, execution limits and inspectable results. Bring a model and Python
functions; no database, graph DSL or shell access is required.

Version 2.0.0rc1 is a release candidate. Start with the offline example in
[Getting Started](getting-started.md), then read the [Harness API](harness.md).

- [Migration from 1.x](migration-v2.md)
- [Execution boundaries](security.md)
- [Technical assessment and roadmap](assessment.md)
- [API reference](api-reference.md)

The existing coding CLI and optional legacy task/server APIs remain available.
Docker is required by default for the CLI runtime; trusted local execution must
be selected explicitly. A workspace alone is not a security sandbox.
