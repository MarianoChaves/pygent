import sys
import types

sys.modules['openai'] = types.ModuleType('openai')
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

from dataclasses import asdict
from pygent import openai_compat
from pygent.models import OpenAIModel
import pygent.models
from pygent.agent import Agent
from pygent.runtime import Runtime
from pygent.commands import cmd_img


def test_parse_message_with_image_list():
    raw = {
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'look'},
            {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,AAA='}},
        ],
    }
    msg = openai_compat.parse_message(raw)
    assert isinstance(msg.content, list)
    dumped = asdict(msg)
    assert dumped['content'][1]['image_url']['url'].startswith('data:image')


def test_openai_model_serializes_image():
    calls = []
    openai = sys.modules['openai']
    openai.chat = types.SimpleNamespace()
    pygent.models.openai = openai

    def create(**kwargs):
        calls.append(kwargs)
        ch = openai_compat.Choice(
            message=openai_compat.Message(role='assistant', content='ok')
        )
        return openai_compat.ChatCompletion(choices=[ch])

    openai.chat.completions = types.SimpleNamespace(create=create)

    model = OpenAIModel()
    msg = openai_compat.Message(role='tool', content='data:image/png;base64,AAA=')
    model.chat([msg], 'gpt', None)
    sent = calls[0]['messages'][0]['content']
    assert isinstance(sent, list)
    assert sent[0]['image_url']['url'].startswith('data:image')


def test_format_content_with_image():
    ag = Agent()
    items = [
        {'type': 'text', 'text': 'see'},
        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,AAA='}},
    ]
    rendered = ag._format_content(items)
    assert 'see' in rendered
    assert 'data:image' in rendered


def test_img_command_sends_data_url(tmp_path):
    calls = []
    ag = Agent(runtime=Runtime(use_docker=False, workspace=tmp_path/'ws'))

    class DummyModel:
        def chat(self, messages, model, tools):
            calls.append(messages[-1]['content'])
            return openai_compat.Message(role='assistant', content='ok')

    ag.model = DummyModel()

    img = tmp_path / 'pic.png'
    img.write_bytes(b'\x89PNG\r\n')
    cmd_img(ag, str(img))
    assert calls
    assert isinstance(calls[0], str) and calls[0].startswith('data:image')
