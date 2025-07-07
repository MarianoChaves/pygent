import os
import sys
import types

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

from pygent.config import run_py_config


def test_run_py_config_sets_env(tmp_path, monkeypatch):
    cfg = tmp_path / 'config.py'
    cfg.write_text("import os\nos.environ['TEST_VAR']='ok'\n")
    run_py_config(cfg)
    assert os.getenv('TEST_VAR') == 'ok'
    monkeypatch.delenv('TEST_VAR', raising=False)


def test_run_py_config_sets_system_builder(tmp_path):
    cfg = tmp_path / 'config.py'
    cfg.write_text(
        'from pygent.agent import set_system_message_builder\n'
        'def b(p, disabled_tools=None):\n'
        '    return "CUSTOM"\n'
        'set_system_message_builder(b)\n'
    )
    run_py_config(cfg)
    from pygent.agent import Agent, set_system_message_builder

    ag = Agent()
    assert ag.system_msg == "CUSTOM"
    set_system_message_builder(None)
