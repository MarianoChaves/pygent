# Contributing

Pygent aims to provide a small, explicit tool-execution loop for Python applications.
Prefer focused changes with a reproducible developer use case over new abstraction
layers. Bugs should include the Python/Pygent versions and a minimal reproduction
without credentials.

## Set up

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test,docs,dev]'
python -m pytest -q
python -m ruff check pygent tests
python -m mkdocs build --strict
python -m build
```

Tests must not require API keys or paid model calls. Use `ScriptedModel` to test
protocol behavior and real temporary files/subprocesses to test runtime boundaries.
Use `pytest.mark.docker` for tests requiring Docker. Test failures, cancellation,
approval denial and limits when changing tool execution. Do not weaken validation
to make a happy-path example work.

Document public APIs and compatibility changes, add a changelog entry, and keep
examples executable. CI covers Python 3.10–3.14 and checks distribution contents.
New provider adapters should remain optional and demonstrate a concrete integration.

## Releases

Version is defined in `pyproject.toml`. A tag matching `v<version>` runs the gated
PyPI workflow. Trusted Publishing must already be configured for this repository.
Never tag a stable release until tests, package build, docs and integration checks
have passed. Release candidates communicate remaining validation requirements;
they are not evidence of production-scale performance or model quality.
