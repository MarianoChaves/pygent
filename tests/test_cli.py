import types
import sys

from typer.testing import CliRunner

sys.modules.setdefault('docker', types.ModuleType('docker'))

from pygent import cli


def test_cli_invokes_run_interactive(monkeypatch):
    calls = []

    def fake_run(use_docker=None, workspace_name=None):
        calls.append((use_docker, workspace_name))

    monkeypatch.setattr(cli, 'run_interactive', fake_run)
    runner = CliRunner()
    result = runner.invoke(cli.app, ['--no-docker', '--workspace', 'foo'])
    assert result.exit_code == 0
    assert calls == [(False, 'foo')]
