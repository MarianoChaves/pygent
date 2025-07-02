import os
import sys
import types

sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

# --- Início da correção ---
rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
panel_mod = types.ModuleType('panel')
markdown_mod = types.ModuleType('markdown') # Novo mock para rich.markdown
syntax_mod = types.ModuleType('syntax')     # Novo mock para rich.syntax

console_mod.Console = lambda *a, **k: None
panel_mod.Panel = lambda *a, **k: None
markdown_mod.Markdown = lambda *a, **k: None # Mock para rich.markdown.Markdown
syntax_mod.Syntax = lambda *a, **k: None     # Mock para rich.syntax.Syntax

sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)
sys.modules.setdefault('rich.markdown', markdown_mod) # Adicionado
sys.modules.setdefault('rich.syntax', syntax_mod)     # Adicionado
# --- Fim da correção ---

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygent import tools, register_tool, Agent, clear_tools, reset_tools, remove_tool

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


def test_register_and_execute_custom_tool():
    def hello(rt, name: str):
        return f"hi {name}"

    register_tool(
        "hello",
        "greet",
        {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        hello,
    )

    call = type('Call', (), {
        'function': type('Func', (), {
            'name': 'hello',
            'arguments': '{"name": "bob"}'
        })
    })()
    assert tools.execute_tool(call, DummyRuntime()) == 'hi bob'


def test_clear_and_reset_tools_updates_prompt():
    clear_tools()
    ag = Agent()
    assert "bash" not in ag.system_msg
    reset_tools()
    ag2 = Agent()
    assert "bash" in ag2.system_msg


def test_remove_tool_updates_prompt():
    reset_tools()
    remove_tool("bash")
    ag = Agent()
    assert "bash" not in ag.system_msg
    reset_tools()


