import os
import sys
import types
import time
import json

sys.modules.setdefault("openai", types.ModuleType("openai"))
sys.modules.setdefault("docker", types.ModuleType("docker"))

# mocks for rich
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
from pygent import openai_compat
from pygent.task_manager import TaskManager
from pygent.persona import Persona
from pygent.runtime import Runtime
from pygent import tools
from pygent.task_tools import register_task_tools

register_task_tools()


class DummyModel:
    def __init__(self):
        self.count = 0

    def chat(self, messages, model, tool_schemas):
        self.count += 1
        if self.count == 1:
            return openai_compat.Message(
                role="assistant",
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id="1",
                        type="function",
                        function=openai_compat.ToolCallFunction(
                            name="write_file",
                            arguments='{"path": "foo.txt", "content": "bar"}',
                        ),
                    )
                ],
            )
        else:
            return openai_compat.Message(
                role="assistant",
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id="2",
                        type="function",
                        function=openai_compat.ToolCallFunction(
                            name="stop", arguments="{}"
                        ),
                    )
                ],
            )


class SlowModel(DummyModel):
    """DummyModel variant that sleeps to simulate long-running tasks."""

    def chat(self, messages, model, tool_schemas):
        time.sleep(0.1)
        return super().chat(messages, model, tool_schemas)


def make_agent():
    return Agent(runtime=Runtime(use_docker=False), model=DummyModel())


def make_slow_agent():
    return Agent(runtime=Runtime(use_docker=False), model=SlowModel())


def test_delegate_and_collect_file(tmp_path):
    tm = TaskManager(agent_factory=make_agent)
    tools._task_manager = tm

    rt = Runtime(use_docker=False)
    task_id = tools._delegate_task(rt, prompt="run")
    tid = task_id.split()[-1]
    tm.tasks[tid].thread.join()

    status = tools._task_status(Runtime(use_docker=False), task_id=tid)
    assert status == "finished"

    main_rt = Runtime(use_docker=False)
    msg = tools._collect_file(main_rt, task_id=tid, path="foo.txt")
    assert "Retrieved" in msg
    copied = main_rt.base_dir / "foo.txt"
    assert copied.exists() and copied.read_text() == "bar"
    main_rt.cleanup()


def test_delegate_with_files():
    tm = TaskManager(agent_factory=make_agent)
    tools._task_manager = tm

    rt = Runtime(use_docker=False)
    rt.write_file("data.txt", "hello")
    tid_msg = tools._delegate_task(rt, prompt="run", files=["data.txt"])
    tid = tid_msg.split()[-1]
    tm.tasks[tid].thread.join()

    child_path = tm.tasks[tid].agent.runtime.base_dir / "data.txt"
    assert child_path.exists() and child_path.read_text() == "hello"


def test_collect_directory(tmp_path):
    tm = TaskManager(agent_factory=make_agent)
    tools._task_manager = tm

    rt = Runtime(use_docker=False)
    tid_msg = tools._delegate_task(rt, prompt="run")
    tid = tid_msg.split()[-1]
    tm.tasks[tid].thread.join()

    subdir = tm.tasks[tid].agent.runtime.base_dir / "sub"
    subdir.mkdir()
    (subdir / "file.txt").write_text("hi")

    main_rt = Runtime(use_docker=False)
    msg = tools._collect_file(main_rt, task_id=tid, path="sub", dest="copy")
    assert "Retrieved" in msg
    assert (main_rt.base_dir / "copy/file.txt").read_text() == "hi"


def test_download_file():
    rt = Runtime(use_docker=False)
    rt.write_file("sample.txt", "hi")
    content = tools._download_file(rt, path="sample.txt")
    assert content == "hi"


class DelegateModel:
    def __init__(self):
        self.count = 0

    def chat(self, messages, model, tool_schemas):
        self.count += 1
        if self.count == 1:
            return openai_compat.Message(
                role="assistant",
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id="1",
                        type="function",
                        function=openai_compat.ToolCallFunction(
                            name="delegate_task", arguments='{"prompt": "noop"}'
                        ),
                    )
                ],
            )
        else:
            return openai_compat.Message(
                role="assistant",
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id="2",
                        type="function",
                        function=openai_compat.ToolCallFunction(
                            name="stop", arguments="{}"
                        ),
                    )
                ],
            )


def make_delegate_agent():
    return Agent(runtime=Runtime(use_docker=False), model=DelegateModel())


def test_no_nested_delegation():
    tm = TaskManager(agent_factory=make_delegate_agent, max_tasks=2)
    tools._task_manager = tm

    tid_msg = tools._delegate_task(Runtime(use_docker=False), prompt="run")
    tid = tid_msg.split()[-1]
    tm.tasks[tid].thread.join()

    # No new tasks should have been created inside the sub-agent
    assert len(tm.tasks) == 1


def test_task_limit():
    tm = TaskManager(agent_factory=make_slow_agent, max_tasks=1)
    tools._task_manager = tm

    first = tools._delegate_task(Runtime(use_docker=False), prompt="run")
    assert first.startswith("started")
    tid = first.split()[-1]

    second = tools._delegate_task(Runtime(use_docker=False), prompt="run")
    assert "max" in second

    tm.tasks[tid].thread.join()


def test_step_timeout():
    ag = make_slow_agent()
    ag.run_until_stop("run", step_timeout=0.05, max_steps=1)
    assert "timeout" in ag.history[-1]["content"]


def test_task_timeout():
    tm = TaskManager(agent_factory=make_slow_agent, max_tasks=1)
    tools._task_manager = tm
    rt = Runtime(use_docker=False)
    tid = tm.start_task("run", rt, task_timeout=0.05, step_timeout=0.01)
    tm.tasks[tid].thread.join()
    assert "timeout" in tm.status(tid)


def test_delegate_persona_task():
    created = []

    def factory(p):
        created.append(p)
        ag = types.SimpleNamespace(
            runtime=Runtime(use_docker=False), model=None, persona=p
        )
        ag.run_until_stop = lambda *a, **k: None
        return ag

    tm = TaskManager(agent_factory=factory)
    tools._task_manager = tm

    rt = Runtime(use_docker=False)
    tid_msg = tools._delegate_persona_task(rt, prompt="run", persona="tester")
    tid = tid_msg.split()[-1]
    tm.tasks[tid].thread.join()

    assert [p.name for p in created] == ["tester"]


def test_list_personas():
    tm = TaskManager(personas=[Persona("a", ""), Persona("b", "")])
    tools._task_manager = tm
    rt = Runtime(use_docker=False)
    result = tools._list_personas(rt)
    assert json.loads(result) == [
        {"name": "a", "description": ""},
        {"name": "b", "description": ""},
    ]


def test_personas_from_env(monkeypatch):
    monkeypatch.setenv(
        "PYGENT_TASK_PERSONAS_JSON", '[{"name":"env","description":"desc"}]'
    )
    tm = TaskManager()
    assert tm.personas[0].name == "env" and tm.personas[0].description == "desc"


def test_global_model_for_tasks():
    from pygent.models import set_custom_model

    set_custom_model(DummyModel())
    tm = TaskManager()
    rt = Runtime(use_docker=False)
    tid = tm.start_task("run", rt)
    tm.tasks[tid].thread.join()
    set_custom_model(None)
    assert isinstance(tm.tasks[tid].agent.model, DummyModel)


def test_task_runtime_matches_parent():
    tm = TaskManager(agent_factory=make_agent)
    rt = Runtime(use_docker=False)
    tid = tm.start_task("echo", rt, task_timeout=0.01, step_timeout=0.01)
    tm.tasks[tid].thread.join()
    assert tm.tasks[tid].agent.runtime.use_docker == rt.use_docker
