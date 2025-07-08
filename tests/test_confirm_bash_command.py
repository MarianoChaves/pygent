import os
import sys
import types

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

from pygent.agent import Agent
from pygent.runtime import Runtime
from pygent.commands import cmd_confirm_bash


def test_cmd_confirm_bash_toggle(tmp_path, capsys):
    ag = Agent(runtime=Runtime(use_docker=False, workspace=tmp_path / 'ws'))
    cmd_confirm_bash(ag, '')
    assert ('on' in capsys.readouterr().out.lower()) == ag.confirm_bash
    cmd_confirm_bash(ag, 'off')
    assert ag.confirm_bash is False
    assert 'disabled' in capsys.readouterr().out.lower()
    cmd_confirm_bash(ag, 'on')
    assert ag.confirm_bash is True
    assert 'enabled' in capsys.readouterr().out.lower()
    ag.runtime.cleanup()
