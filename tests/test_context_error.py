import os
import sys
import types
import pytest

sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
panel_mod = types.ModuleType('panel')
markdown_mod = types.ModuleType('markdown')
syntax_mod = types.ModuleType('syntax')
console_mod.Console = lambda *a, **k: type('C', (), {'print': lambda *a, **k: None})()
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
from pygent.errors import APIError
from pygent.runtime import Runtime

class FailingModel:
    def __init__(self):
        self.calls = []
    def chat(self, messages, model, tools):
        self.calls.append(len(messages))
        if len(messages) > 3:
            raise APIError('maximum context length')
        return openai_compat.Message(role='assistant', content='ok')

def test_trim_history_on_context_error(monkeypatch):
    monkeypatch.setenv('PYGENT_MAX_HISTORY', '50')
    model = FailingModel()
    ag = Agent(runtime=Runtime(use_docker=False), model=model)
    ag.step('hello')
    ag.step('again')
    assert model.calls == [2, 4, 3]
    assert len(ag.history) <= 3
