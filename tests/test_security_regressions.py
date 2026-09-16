import json
import os
import shlex
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from types import SimpleNamespace

import pytest

from pygent import Agent
from pygent.runtime import Runtime
from pygent.testing import ScriptedModel
from pygent.task_manager import TaskManager


@pytest.mark.parametrize("operation", ["read", "write", "upload", "export"])
@pytest.mark.parametrize("kind", ["parent", "absolute", "symlink"])
def test_file_api_rejects_workspace_escape(tmp_path, operation, kind):
    root = tmp_path / "work"
    outside = tmp_path / "private"
    outside.mkdir()
    secret = outside / "secret"
    secret.write_text("private")
    with Runtime(use_docker=False, workspace=root) as rt:
        if kind == "symlink":
            (root / "link").symlink_to(outside, target_is_directory=True)
            path = "link/secret"
        else:
            path = "../private/secret" if kind == "parent" else str(secret)
        with pytest.raises(ValueError):
            if operation == "read":
                rt.read_file(path)
            elif operation == "write":
                rt.write_file(path, "changed")
            elif operation == "upload":
                rt.upload_file(secret, path)
            else:
                rt.export_file(path, tmp_path / "export")
        assert secret.read_text() == "private"


def test_nested_symlink_copy_rejected(tmp_path):
    with Runtime(use_docker=False, workspace=tmp_path / "work") as rt:
        (rt.base_dir / "dir").mkdir()
        (rt.base_dir / "dir" / "link").symlink_to(tmp_path / "secret")
        with pytest.raises(ValueError, match="symlink"):
            rt.export_file("dir", tmp_path / "copy")


def test_docker_missing_never_falls_back(monkeypatch, tmp_path):
    monkeypatch.setattr("pygent.runtime.docker", None)
    with pytest.raises(RuntimeError, match="Docker is required"):
        Runtime(use_docker=True, workspace=tmp_path)


def test_docker_startup_failure_closes_client(monkeypatch, tmp_path):
    closed = []

    def fail(*args, **kwargs):
        raise OSError("daemon unavailable")

    client = SimpleNamespace(
        containers=SimpleNamespace(run=fail), close=lambda: closed.append(True)
    )
    monkeypatch.setattr("pygent.runtime.docker", SimpleNamespace(from_env=lambda: client))
    with pytest.raises(RuntimeError, match="local execution was not enabled"):
        Runtime(use_docker=True, workspace=tmp_path)
    assert closed == [True]


def test_docker_shell_and_timeout_use_supported_sdk_arguments(monkeypatch, tmp_path):
    captured = []

    class Container:
        def exec_run(self, cmd, *, workdir, stream, tty, stdin):
            captured.append(cmd)
            return SimpleNamespace(output=iter([b"hi\n"]))

        def kill(self):
            pass

        def remove(self, **kwargs):
            pass

    container = Container()
    client = SimpleNamespace(
        containers=SimpleNamespace(run=lambda *a, **k: container), close=lambda: None
    )
    monkeypatch.setattr("pygent.runtime.docker", SimpleNamespace(from_env=lambda: client))
    with Runtime(use_docker=True, workspace=tmp_path) as rt:
        assert rt.bash("echo hi | cat", timeout=1).endswith("hi\n")
    assert captured == [["timeout", "--signal=KILL", "1", "sh", "-lc", "echo hi | cat"]]


def test_local_output_without_newline_is_bounded(tmp_path):
    with Runtime(use_docker=False, workspace=tmp_path) as rt:
        cmd = f'{shlex.quote(sys.executable)} -c \'print("x" * 1000000, end="")\''
        output = rt.bash(cmd, max_output_chars=1024)
        assert len(output) < 1100 and "[output truncated]" in output


@pytest.mark.skipif(os.name != "posix", reason="POSIX process group semantics")
def test_timeout_kills_descendants_without_waiting_for_pipe(tmp_path):
    with Runtime(use_docker=False, workspace=tmp_path) as rt:
        start = time.monotonic()
        output = rt.bash("sleep 20 & wait", timeout=0.05)
        assert time.monotonic() - start < 3
        assert "timeout" in output


def test_disabled_and_malformed_tool_calls_do_not_execute(tmp_path):
    model = ScriptedModel(
        [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "one",
                        "type": "function",
                        "function": {
                            "name": "write_file",
                            "arguments": '{"path": "bad", "content": "bad"}',
                        },
                    },
                    {
                        "id": "two",
                        "type": "function",
                        "function": {"name": "bash", "arguments": "["},
                    },
                ],
            }
        ]
    )
    with Runtime(use_docker=False, workspace=tmp_path) as rt:
        agent = Agent(runtime=rt, model=model, disabled_tools=["write_file"], confirm_bash=True)
        try:
            agent.step("Run")
            assert not (tmp_path / "bad").exists()
            assert "disabled" in agent.history[-2]["content"]
            assert "invalid arguments" in agent.history[-1]["content"]
        finally:
            agent.close()


def test_history_resume_preserves_tool_call_id_and_can_step(tmp_path):
    path = tmp_path / "history.json"
    model = ScriptedModel(
        [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "one",
                        "type": "function",
                        "function": {
                            "name": "write_file",
                            "arguments": '{"path": "ok", "content": "ok"}',
                        },
                    }
                ],
            }
        ]
    )
    with Runtime(use_docker=False, workspace=tmp_path / "work") as rt:
        agent = Agent(runtime=rt, model=model, history_file=path)
        agent.step("Run")
        agent.close()
        next_model = ScriptedModel([{"role": "assistant", "content": "done"}])
        restored = Agent(runtime=rt, model=next_model, history_file=path)
        try:
            restored.step("Continue")
            tool = next(
                m
                for m in next_model.requests[0]["messages"]
                if isinstance(m, dict) and m.get("role") == "tool"
            )
            assert tool["tool_call_id"] == "one"
            assert json.loads(path.read_text())[-1]["content"] == "done"
        finally:
            restored.close()


def test_task_admission_limit_is_atomic(tmp_path):
    release, barrier = Event(), Barrier(4)

    def factory(*args):
        time.sleep(0.02)
        return SimpleNamespace(
            runtime=None, system_msg="test", run_until_stop=lambda *a, **kw: release.wait(5)
        )

    manager = TaskManager(agent_factory=factory, max_tasks=1)
    with Runtime(use_docker=False, workspace=tmp_path) as rt:

        def start(_):
            barrier.wait()
            try:
                return manager.start_task("Run", rt)
            except RuntimeError:
                return None

        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(start, range(4)))
            assert sum(result is not None for result in results) == 1
        finally:
            release.set()
            for task in manager.tasks.values():
                task.thread.join(timeout=2)
                task.agent.runtime.cleanup()


def test_invalid_history_is_not_silently_overwritten(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"broken":')
    with Runtime(use_docker=False, workspace=tmp_path / "work") as rt:
        with pytest.raises(ValueError, match="Cannot restore"):
            Agent(runtime=rt, model=ScriptedModel([]), history_file=path)
    assert path.read_text() == '{"broken":'


def test_default_task_factory_inherits_explicit_local_runtime(monkeypatch, tmp_path):
    from pygent.models import set_custom_model

    monkeypatch.delenv("PYGENT_USE_DOCKER")
    set_custom_model(
        ScriptedModel(
            [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "one",
                            "type": "function",
                            "function": {"name": "stop", "arguments": "{}"},
                        }
                    ],
                }
            ]
        )
    )
    try:
        with Runtime(use_docker=False, workspace=tmp_path, banned_commands=["rm"]) as rt:
            manager = TaskManager()
            tid = manager.start_task("Run", rt)
            task = manager.tasks[tid]
            task.thread.join(timeout=2)
            assert task.status == "finished"
            assert task.agent.runtime.use_docker is False
            assert "rm" in task.agent.runtime.banned_commands
            task.agent.close()
            task.agent.runtime.cleanup()
    finally:
        set_custom_model(None)
