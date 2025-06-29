import importlib
import sys
import types

# Stub external dependencies so the package can be imported without network
sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

# --- Início da correção ---
rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
panel_mod = types.ModuleType('panel')
markdown_mod = types.ModuleType('markdown') # Novo mock para rich.markdown
syntax_mod = types.ModuleType('syntax')     # Novo mock para rich.syntax

console_mod.Console = lambda *a, **k: None
panel_mod.Panel = lambda *a, **k: None
markdown_mod.Markdown = lambda *a, **k: None # Mock para rich.markdown.Markdown
syntax_mod.Syntax = lambda *a, **k: None     # Mock para rich.syntax.Syntax

sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)
sys.modules.setdefault('rich.markdown', markdown_mod)
sys.modules.setdefault('rich.syntax', syntax_mod)

def test_version_string():
    pkg = importlib.import_module('pygent')
    assert isinstance(pkg.__version__, str)

