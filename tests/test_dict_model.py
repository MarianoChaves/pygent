import os
import sys
import types

sys.modules.setdefault("openai", types.ModuleType("openai"))
sys.modules.setdefault("docker", types.ModuleType("docker"))

rich_mod = types.ModuleType("rich")
console_mod = types.ModuleType("console")
panel_mod = types.ModuleType("panel")
markdown_mod = types.ModuleType("markdown")
syntax_mod = types.ModuleType("syntax")
console_mod.Console = lambda *a, **k: type("C", (), {"print": lambda *a, **k: None})()
panel_mod.Panel = lambda *a, **k: None
markdown_mod.Markdown = lambda *a, **k: None
syntax_mod.Syntax = lambda *a, **k: None
sys.modules.setdefault("rich", rich_mod)
sys.modules.setdefault("rich.console", console_mod)
sys.modules.setdefault("rich.panel", panel_mod)
sys.modules.setdefault("rich.markdown", markdown_mod)
sys.modules.setdefault("rich.syntax", syntax_mod)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pygent import Agent


class DictModel:
    def chat(self, messages, model, tools):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "1",
                    "type": "function",
                    "function": {"name": "bash", "arguments": '{"cmd": "echo hi"}'},
                }
            ],
        }


class DummyRuntime:
    def bash(self, cmd: str):
        return f"ran {cmd}"

    def write_file(self, path: str, content: str):
        return f"wrote {path}"


def test_dict_model_tool():
    ag = Agent(runtime=DummyRuntime(), model=DictModel(), confirm_bash=False)
    ag.step("run")
    assert any(isinstance(m, dict) and m.get("role") == "tool" for m in ag.history)
