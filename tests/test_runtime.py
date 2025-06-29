import os
import sys
import types

# Stub external dependencies
sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('docker', types.ModuleType('docker'))

# --- Início da correção ---
# Criação de módulos mock para rich e seus submódulos
rich_mod = types.ModuleType('rich')
console_mod = types.ModuleType('console')
panel_mod = types.ModuleType('panel')
markdown_mod = types.ModuleType('markdown') # Novo mock para rich.markdown
syntax_mod = types.ModuleType('syntax')     # Novo mock para rich.syntax

# Mocks para as classes e funções usadas de rich
console_mod.Console = lambda *a, **k: type('C', (), {'print': lambda *a, **k: None})()
panel_mod.Panel = lambda *a, **k: None
markdown_mod.Markdown = lambda *a, **k: None # Mock para rich.markdown.Markdown
syntax_mod.Syntax = lambda *a, **k: None     # Mock para rich.syntax.Syntax

# Definindo os módulos mock no sys.modules
sys.modules.setdefault('rich', rich_mod)
sys.modules.setdefault('rich.console', console_mod)
sys.modules.setdefault('rich.panel', panel_mod)
sys.modules.setdefault('rich.markdown', markdown_mod) # Adicionado
sys.modules.setdefault('rich.syntax', syntax_mod)     # Adicionado
# --- Fim da correção ---

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygent.runtime import Runtime


def test_bash_includes_command():
    rt = Runtime(use_docker=False)
    out = rt.bash('echo hi')
    rt.cleanup()
    assert out.startswith('$ echo hi\n')

