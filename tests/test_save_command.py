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
from pygent.commands import cmd_save


def test_cmd_save_creates_snapshot(tmp_path):
    ag = Agent(runtime=Runtime(use_docker=False, workspace=tmp_path/'ws'))
    ag.runtime.write_file('foo.txt', 'bar')
    dest = tmp_path / 'save'
    cmd_save(ag, str(dest))
    assert (dest/'workspace'/'foo.txt').read_text() == 'bar'
    assert (dest/'env.json').exists()
    ag.runtime.cleanup()
