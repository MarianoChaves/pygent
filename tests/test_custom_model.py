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

console_mod.Console = lambda *a, **k: type('C', (), {'print': lambda *a, **k: None})()
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

from pygent import Agent, openai_compat

class DummyModel:
    def chat(self, messages, model, tools):
        return openai_compat.Message(role='assistant', content='ok')


def test_custom_model():
    ag = Agent(model=DummyModel())
    ag.step('hi')
    assert ag.history[-1].content == 'ok'


def test_global_custom_model():
    class GlobalModel:
        def chat(self, messages, model, tools):
            return openai_compat.Message(role='assistant', content='global')

    from pygent.models import set_custom_model

    set_custom_model(GlobalModel())
    ag = Agent()
    ag.step('ping')
    set_custom_model(None)
    assert ag.history[-1].content == 'global'

