import os
import sys
import types
import json

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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygent import Agent, openai_compat

class DummyModel:
    def chat(self, messages, model, tools):
        return openai_compat.Message(role='assistant', content='saved')

class DummyRuntime:
    def bash(self, cmd: str):
        return f"ran {cmd}"
    def write_file(self, path: str, content: str):
        return f"wrote {path}"

def test_history_saved_and_loaded(tmp_path):
    path = tmp_path / 'hist.json'
    ag = Agent(runtime=DummyRuntime(), model=DummyModel(), history_file=path)
    ag.step('hello')
    assert path.exists()
    data = json.loads(path.read_text())
    assert any(m.get('role') == 'assistant' for m in data)

    ag2 = Agent(runtime=DummyRuntime(), model=DummyModel(), history_file=path)
    assert any((m.role if hasattr(m, 'role') else m.get('role')) == 'assistant' for m in ag2.history)
