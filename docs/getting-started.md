# Getting started

Python 3.10+ is required. Install the release candidate from a source checkout:

```bash
python -m pip install -e .
python examples/offline_harness.py
python examples/workspace_harness.py
```

The examples execute real Python tools with a deterministic scripted model and do
not need credentials, network access or Docker. See the [Harness API](harness.md)
for real-model integration, approvals, limits and continuation.

## Coding CLI

```bash
python -m pip install -e '.[docker]'
pygent --docker
```

Configure `OPENAI_API_KEY` and `PYGENT_MODEL` for your provider. Docker must be
installed and running. To explicitly run trusted commands on the host, use
`pygent --no-docker`. Read [execution boundaries](security.md) first.

Use `/help` inside the session. Additional options, configuration and snapshots are
covered in [CLI](cli.md) and [Configuration](configuration.md).
