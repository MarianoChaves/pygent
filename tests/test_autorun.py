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
    def __init__(self):
        self.count = 0
    def chat(self, messages, model, tools):
        self.count += 1
        if self.count == 1:
            return openai_compat.Message(
                role='assistant',
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id='1',
                        type='function',
                        function=openai_compat.ToolCallFunction(
                            name='bash',
                            arguments='{"cmd": "ls"}'
                        )
                    )
                ]
            )
        else:
            return openai_compat.Message(
                role='assistant',
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id='2',
                        type='function',
                        function=openai_compat.ToolCallFunction(
                            name='stop',
                            arguments='{}'
                        )
                    )
                ]
            )

class DummyRuntime:
    def bash(self, cmd: str):
        return f"ran {cmd}"
    def write_file(self, path: str, content: str):
        return f"wrote {path}"


def test_run_until_stop():
    ag = Agent(runtime=DummyRuntime(), model=DummyModel())
    ag.run_until_stop('start', max_steps=5)
    assert any(call.function.name == 'stop'
               for msg in ag.history
               if hasattr(msg, 'tool_calls') and msg.tool_calls
               for call in msg.tool_calls)
