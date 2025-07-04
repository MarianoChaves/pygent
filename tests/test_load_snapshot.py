import os
import sys
import types
import json

sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

# minimal rich mocks
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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygent.config import load_snapshot
from pygent.runtime import Runtime


def test_load_snapshot_sets_env(tmp_path, monkeypatch):
    snap = tmp_path / 'snap'
    ws = snap / 'workspace'
    ws.mkdir(parents=True)
    (snap / 'env.json').write_text(json.dumps({'OPENAI_API_KEY': 'test'}))
    (snap / 'history.json').write_text('[]')

    saved = os.environ.copy()
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    load_snapshot(snap)
    assert os.getenv('OPENAI_API_KEY') == 'test'
    assert os.getenv('PYGENT_WORKSPACE') == str(ws)
    assert os.getenv('PYGENT_HISTORY_FILE') == str(snap / 'history.json')

    rt = Runtime(use_docker=False)
    assert rt.base_dir == ws
    rt.cleanup()
    os.environ.clear()
    os.environ.update(saved)
