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


def test_upload_and_export_file(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("hello")
    rt = Runtime(use_docker=False)
    msg = rt.upload_file(src)
    assert "Uploaded" in msg
    dest = tmp_path / "dest.txt"
    msg2 = rt.export_file(src.name, dest)
    assert "Exported" in msg2
    assert dest.exists() and dest.read_text() == "hello"
    rt.cleanup()


def test_runtime_use_docker_property():
    rt = Runtime(use_docker=False)
    try:
        assert rt.use_docker is False
    finally:
        rt.cleanup()


def test_banned_command_blocked():
    rt = Runtime(use_docker=False, banned_commands=["rm"])
    out = rt.bash("rm -rf foo")
    rt.cleanup()
    assert "command 'rm' disabled" in out


def test_banned_app_blocked_env(monkeypatch):
    monkeypatch.setenv("PYGENT_BANNED_APPS", "python")
    rt = Runtime(use_docker=False)
    out = rt.bash("python script.py")
    rt.cleanup()
    assert "application 'python' disabled" in out

