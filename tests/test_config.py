import os
import sys
import types
import json

sys.modules.setdefault("openai", types.ModuleType("openai"))
sys.modules.setdefault("docker", types.ModuleType("docker"))

# minimal mocks for rich
rich_mod = types.ModuleType("rich")
console_mod = types.ModuleType("console")
panel_mod = types.ModuleType("panel")
markdown_mod = types.ModuleType("markdown")
console_mod.Console = lambda *a, **k: None
panel_mod.Panel = lambda *a, **k: None
markdown_mod.Markdown = lambda *a, **k: None
sys.modules.setdefault("rich", rich_mod)
sys.modules.setdefault("rich.console", console_mod)
sys.modules.setdefault("rich.panel", panel_mod)
sys.modules.setdefault("rich.markdown", markdown_mod)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pygent.config import load_config
from pygent.runtime import Runtime
from pygent.task_manager import TaskManager
from pygent.persona import Persona


def test_load_config(tmp_path, monkeypatch):
    cfg = tmp_path / "pygent.toml"
    cfg.write_text(
        'persona="bot"\n'
        'persona_name="Bot"\n'
        'initial_files=["seed.txt"]\n'
        '[[task_personas]]\nname="a"\ndescription="desc a"\n'
        '[[task_personas]]\nname="b"\ndescription="desc b"\n'
    )
    (tmp_path / "seed.txt").write_text("seed")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYGENT_PERSONA", raising=False)
    monkeypatch.delenv("PYGENT_TASK_PERSONAS", raising=False)
    monkeypatch.delenv("PYGENT_TASK_PERSONAS_JSON", raising=False)
    monkeypatch.delenv("PYGENT_INIT_FILES", raising=False)
    monkeypatch.delenv("PYGENT_PERSONA_NAME", raising=False)
    load_config()
    assert os.getenv("PYGENT_PERSONA") == "bot"
    assert os.getenv("PYGENT_PERSONA_NAME") == "Bot"
    assert os.getenv("PYGENT_TASK_PERSONAS") == os.pathsep.join(["a", "b"])
    data = json.loads(os.getenv("PYGENT_TASK_PERSONAS_JSON"))
    assert data[0]["description"] == "desc a"
    assert os.getenv("PYGENT_INIT_FILES") == "seed.txt"
    rt = Runtime(use_docker=False)
    assert (rt.base_dir / "seed.txt").exists()
    rt.cleanup()


def test_task_manager_personas(monkeypatch):
    created = []

    def factory(p):
        created.append(p)
        ag = types.SimpleNamespace(
            runtime=Runtime(use_docker=False), model=None, persona=p
        )
        ag.run_until_stop = lambda *a, **k: None
        return ag

    tm = TaskManager(
        agent_factory=factory, personas=[Persona("one", ""), Persona("two", "")]
    )
    tm.start_task("noop", Runtime(use_docker=False))
    tm.start_task("noop", Runtime(use_docker=False))
    tm.tasks[next(iter(tm.tasks))].thread.join()
    assert [p.name for p in created] == ["one", "two"]
