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

from pygent import tools

class DummyRuntime:
    def bash(self, cmd: str):
        return f"ran {cmd}"
    def write_file(self, path: str, content: str):
        return f"wrote {path}"

def test_execute_bash():
    call = type('Call', (), {
        'function': type('Func', (), {
            'name': 'bash',
            'arguments': '{"cmd": "ls"}'
        })
    })()
    assert tools.execute_tool(call, DummyRuntime()) == 'ran ls'


def test_execute_write_file():
    call = type('Call', (), {
        'function': type('Func', (), {
            'name': 'write_file',
            'arguments': '{"path": "foo.txt", "content": "bar"}'
        })
    })()
    assert tools.execute_tool(call, DummyRuntime()) == 'wrote foo.txt'
