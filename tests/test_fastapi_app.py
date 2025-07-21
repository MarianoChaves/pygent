import os
import sys
import types

import pytest

pytest.importorskip("fastapi")

sys.modules.setdefault("openai", types.ModuleType("openai"))
sys.modules.setdefault("docker", types.ModuleType("docker"))

# mocks for rich
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

from fastapi.testclient import TestClient
from pygent.fastapi_app import create_app
from pygent import openai_compat
from pygent.models import set_custom_model


class DummyModel:
    def chat(self, messages, model, tools):
        return openai_compat.Message(role='assistant', content='ok')


class AskModel:
    def chat(self, messages, model, tools):
        return openai_compat.Message(
            role='assistant',
            content=None,
            tool_calls=[
                openai_compat.ToolCall(
                    id='1',
                    type='function',
                    function=openai_compat.ToolCallFunction(
                        name='ask_user',
                        arguments='{"prompt": "Pick", "options": ["a", "b"]}',
                    ),
                )
            ],
        )


def test_api_lifecycle():
    set_custom_model(DummyModel())
    app = create_app()
    client = TestClient(app)

    resp = client.post('/tasks', json={'prompt': 'run'})
    tid = resp.json()['task_id']

    # wait for task to finish
    app.state.manager.tasks[tid].thread.join()

    status = client.get(f'/tasks/{tid}').json()['status']
    assert status == 'finished'

    lst = client.get('/tasks').json()
    assert any(t['id'] == tid for t in lst)

    resp = client.post(f'/tasks/{tid}/message', json={'message': 'hello'})
    data = resp.json()
    assert data['response'] == 'ok'
    assert data['ask_user'] is None

    set_custom_model(None)


def test_message_returns_ask_user():
    set_custom_model(AskModel())
    app = create_app()
    client = TestClient(app)

    resp = client.post('/tasks', json={'prompt': 'run'})
    tid = resp.json()['task_id']
    app.state.manager.tasks[tid].thread.join()

    resp = client.post(f'/tasks/{tid}/message', json={'message': 'hello'})
    data = resp.json()
    assert data['ask_user']['options'] == ['a', 'b']

    set_custom_model(None)

