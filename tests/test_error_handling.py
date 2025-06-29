import os
import sys
import types
import pytest

# Stub external dependencies
sys.modules.setdefault('docker', types.ModuleType('docker'))
rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
console_mod.Console = lambda *a, **k: None
panel_mod = types.ModuleType('panel')
panel_mod.Panel = lambda *a, **k: None
sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)


def test_openai_model_error():
    openai_mod = types.ModuleType('openai')
    class ChatComp:
        def create(*a, **k):
            raise RuntimeError('boom')
    chat_mod = types.ModuleType('chat')
    chat_mod.completions = ChatComp()
    openai_mod.chat = chat_mod
    sys.modules['openai'] = openai_mod

    from pygent.models import OpenAIModel
    from pygent.errors import APIError

    model = OpenAIModel()
    with pytest.raises(APIError):
        model.chat([], 'gpt', None)


def test_bash_timeout():
    from pygent.runtime import Runtime
    rt = Runtime(use_docker=False)
    out = rt.bash('sleep 5', timeout=0)
    rt.cleanup()
    assert '[timeout' in out
