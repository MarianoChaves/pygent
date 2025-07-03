import sys
import types

# stub external dependencies
sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
panel_mod = types.ModuleType('panel')
markdown_mod = types.ModuleType('markdown')
syntax_mod = types.ModuleType('syntax')
console_mod.Console = lambda *a, **k: None
panel_mod.Panel = lambda *a, **k: None
markdown_mod.Markdown = lambda *a, **k: None
syntax_mod.Syntax = lambda *a, **k: None
sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)
sys.modules.setdefault('rich.markdown', markdown_mod)
sys.modules.setdefault('rich.syntax', syntax_mod)

from pygent.commands import cmd_help


def test_help_lists_commands(capsys):
    cmd_help(None, "")
    captured = capsys.readouterr().out
    assert "/cmd" in captured
    assert "/cp" in captured
    assert "quit the session" in captured


def test_help_specific_command(capsys):
    cmd_help(None, "/cmd")
    captured = capsys.readouterr().out
    assert "/cmd -" in captured

