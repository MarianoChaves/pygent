import os
import sys
import types

sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))
rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
console_mod.Console = lambda *a, **k: type('C', (), {'print': lambda *a, **k: None})()
panel_mod = types.ModuleType('panel')
panel_mod.Panel = lambda *a, **k: None
sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygent import Agent, openai_compat

class DummyModel:
    def chat(self, messages, model, tools):
        return openai_compat.Message(role='assistant', content='ok')


def test_custom_model():
    ag = Agent(model=DummyModel())
    ag.step('hi')
    assert ag.history[-1].content == 'ok'
