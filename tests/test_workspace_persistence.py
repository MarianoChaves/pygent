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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygent.runtime import Runtime


def test_persistent_workspace(tmp_path):
    ws = tmp_path / 'ws'
    rt = Runtime(use_docker=False, workspace=ws)
    rt.write_file('foo.txt', 'bar')
    rt.cleanup()
    assert (ws / 'foo.txt').exists()

    rt2 = Runtime(use_docker=False, workspace=ws)
    assert rt2.read_file('foo.txt') == 'bar'
    rt2.cleanup()
    assert (ws / 'foo.txt').exists()
