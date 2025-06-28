import os
import sys
import types

sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))
rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
console_mod.Console = lambda *a, **k: None
panel_mod = types.ModuleType('panel')
panel_mod.Panel = lambda *a, **k: None
sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygent.runtime import Runtime


def test_bash_includes_command():
    rt = Runtime(use_docker=False)
    out = rt.bash('echo hi')
    rt.cleanup()
    assert out.startswith('$ echo hi\n')
