import sys
import types

sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
panel_mod = types.ModuleType('panel')
markdown_mod = types.ModuleType('markdown')
syntax_mod = types.ModuleType('syntax')
console_mod.Console = lambda *a, **k: type('C', (), {'print': lambda *a, **k: None, 'input': lambda self, prompt='': ''})()
panel_mod.Panel = lambda *a, **k: None
markdown_mod.Markdown = lambda *a, **k: None
syntax_mod.Syntax = lambda *a, **k: None
sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)
sys.modules.setdefault('rich.markdown', markdown_mod)
sys.modules.setdefault('rich.syntax', syntax_mod)

from pygent.session import Session
from pygent import openai_compat

class DummyAgent:
    def __init__(self):
        self.persona = types.SimpleNamespace(name='bot')
        self.runtime = types.SimpleNamespace(use_docker=False, cleanup=lambda: None)
        self._log_fp = None
        self.closed = False
        self.calls = []
    def run_until_stop(self, msg):
        self.calls.append(msg)
        if msg == 'start':
            tc = openai_compat.ToolCall(
                id='1',
                type='function',
                function=openai_compat.ToolCallFunction(
                    name='ask_user',
                    arguments='{"prompt": "Pick", "options": ["a", "b"]}'
                )
            )
            return openai_compat.Message(role='assistant', content=None, tool_calls=[tc])
        return None
    def close(self):
        self.closed = True


def test_session_ask_uses_get_input():
    agent = DummyAgent()
    prompts = []
    class MySession(Session):
        def get_input(self, prompt: str) -> str:
            prompts.append(prompt)
            return 'x'
    session = MySession(agent)
    out = session.ask('Choose', ['a', 'b'])
    assert out == 'x'
    assert prompts == ['Choose (a/b): ']


def test_session_run_handles_ask_user():
    agent = DummyAgent()
    closed = []
    agent.runtime.cleanup = lambda: closed.append('cleanup')
    agent.close = lambda: closed.append('close')

    inputs = ['start', '/exit']
    class MySession(Session):
        def get_input(self, prompt: str) -> str:
            return inputs.pop(0)
        def ask(self, prompt: str, options):
            return 'a'
    session = MySession(agent)
    session.run()
    assert agent.calls == ['start', 'a']
    assert 'close' in closed and 'cleanup' in closed
