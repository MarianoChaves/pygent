import os
import sys
import types

sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

# minimal rich mocks
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

from pygent.commands import register_command, COMMANDS
from pygent.agent import Agent
from pygent.runtime import Runtime


def test_register_command_and_save(tmp_path, capsys):
    def hello(agent, arg):
        print('hello', arg)
    register_command('/hello', hello, 'greet')
    ag = Agent(runtime=Runtime(use_docker=False, workspace=tmp_path/'ws'))
    COMMANDS['/hello'](ag, 'world')
    captured = capsys.readouterr().out
    assert 'hello world' in captured
    # cleanup to avoid side effects
    COMMANDS.pop('/hello')
    ag.runtime.cleanup()
