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
from pygent.runtime import Runtime

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


def test_execute_tool_handles_exception():
    def boom(rt):
        raise RuntimeError('fail')

    register_tool(
        "boom",
        "fail",
        {"type": "object", "properties": {}},
        lambda rt: boom(rt),
    )

    call = type('Call', (), {
        'function': type('Func', (), {
            'name': 'boom',
            'arguments': '{}'
        })
    })()

    out = tools.execute_tool(call, DummyRuntime())
    assert 'error' in out.lower()
    remove_tool('boom')


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


def test_ask_user_tool_schema_allows_options():
    schema = [s for s in tools.TOOL_SCHEMAS if s["function"]["name"] == "ask_user"][0]
    props = schema["function"]["parameters"]["properties"]
    assert "options" in props


def test_read_image_data_url(tmp_path):
    rt = Runtime(use_docker=False, workspace=tmp_path)
    img = tmp_path / "img.png"
    img.write_bytes(b"\x89PNG\r\n")
    result = tools._read_image(rt, path="img.png")
    assert result.startswith("data:image/png;base64,")


def test_workflow_block_respects_ask_user():
    reset_tools()
    ag = Agent()
    assert "ask_user" in ag.system_msg
    assert "procceed" in ag.system_msg

    remove_tool("ask_user")
    ag2 = Agent()
    assert "ask_user" not in ag2.system_msg
    assert "procceed" not in ag2.system_msg
    reset_tools()


def test_workflow_block_respects_stop_tool():
    reset_tools()
    ag = Agent()
    assert "stop" in ag.system_msg

    remove_tool("stop")
    ag2 = Agent()
    assert "stop" not in ag2.system_msg
    reset_tools()


def test_workflow_block_includes_review_instruction():
    ag = Agent()
    assert "verify and test" in ag.system_msg


