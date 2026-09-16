import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from pygent import Harness, RunLimits, Tool
from pygent.testing import ScriptedModel

SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "integer"}},
    "required": ["value"],
    "additionalProperties": False,
}


def call(arguments='{"value": 2}', name="double", id="one"):
    return {"id": id, "type": "function", "function": {"name": name, "arguments": arguments}}


def reply(calls):
    return {"role": "assistant", "tool_calls": calls}


def make_harness(responses, action=lambda value: value * 2, approval=False):
    return Harness(
        ScriptedModel(responses),
        model_name="offline",
        tools=[
            Tool(
                "double",
                "Double an integer",
                SCHEMA,
                lambda value: action(value),
                requires_approval=approval,
            )
        ],
    )


def test_full_tool_protocol_and_json_output():
    harness = make_harness([reply([call()]), {"role": "assistant", "content": '{"value": 4}'}])
    result = harness.run("Double two", output_schema=SCHEMA)
    assert (result.status, result.steps, result.tool_calls, result.data) == (
        "completed",
        2,
        1,
        {"value": 4},
    )
    assert harness.model.requests[1]["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "one",
        "content": "4",
    }
    assert json.loads(json.dumps(result.to_dict()))["status"] == "completed"
    assert result.events[-1].kind == "run_finished"


@pytest.mark.parametrize(
    "arguments", ["{", "[]", '{"value": "2"}', '{"value": 2, "extra": 1}', '{"value": NaN}', "{}"]
)
def test_invalid_arguments_never_execute(arguments):
    side_effects = []
    harness = make_harness([reply([call(arguments)])], side_effects.append)
    result = harness.run("Run", limits=RunLimits(max_steps=1))
    assert side_effects == []
    assert result.messages[-1]["content"].startswith("[error] invalid tool call")


def test_unknown_tool_and_no_implicit_builtins():
    harness = Harness(ScriptedModel([reply([call(name="bash")])]), model_name="offline")
    result = harness.run("Run", limits=RunLimits(max_steps=1))
    assert harness.model.requests[0]["tools"] == []
    assert "unknown tool" in result.messages[-1]["content"]


@pytest.mark.parametrize("approved", [None, False, "yes", 1])
def test_approval_is_fail_closed(approved):
    effects = []
    harness = make_harness([reply([call()])], effects.append, approval=True)
    result = harness.run(
        "Run",
        limits=RunLimits(max_steps=1),
        approve=None if approved is None else lambda *_: approved,
    )
    assert effects == []
    assert "denied" in result.messages[-1]["content"]


def test_approved_call_and_callback_cannot_mutate_arguments():
    effects = []

    def approve(name, args):
        args["value"] = 999
        return True

    result = make_harness([reply([call()])], effects.append, True).run(
        "Run", limits=RunLimits(max_steps=1), approve=approve
    )
    assert effects == [2]
    assert result.events[-2].outcome == "success"


def test_whole_batch_budget_rejection_preserves_protocol():
    effects = []
    harness = make_harness([reply([call(id="a"), call(id="b")])], effects.append)
    result = harness.run("Run", limits=RunLimits(max_tool_calls=1))
    assert result.status == "max_tool_calls"
    assert effects == [] and result.tool_calls == 0
    assert [msg["tool_call_id"] for msg in result.messages if msg["role"] == "tool"] == ["a", "b"]


def test_cancellation_between_tools():
    cancel = Event()
    effects = []

    def action(value):
        effects.append(value)
        cancel.set()

    result = make_harness([reply([call(id="a"), call(id="b")])], action).run("Run", cancel=cancel)
    assert result.status == "cancelled"
    assert effects == [2]
    assert result.messages[-1]["tool_call_id"] == "b"
    assert "not executed" in result.messages[-1]["content"]


def test_cancel_before_run_never_calls_model():
    cancel = Event()
    cancel.set()
    harness = make_harness([])
    assert harness.run("Run", cancel=cancel).status == "cancelled"
    assert harness.model.requests == []


def test_elapsed_budget_prevents_tools_after_slow_model(monkeypatch):
    now = [0.0]
    monkeypatch.setattr("pygent.harness.time.monotonic", lambda: now[0])
    effects = []
    harness = make_harness([reply([call()])], effects.append)
    original = harness.model.chat

    def slow(*args):
        now[0] = 2.0
        return original(*args)

    harness.model.chat = slow
    result = harness.run("Run", limits=RunLimits(max_time=1.0))
    assert result.status == "timeout"
    assert effects == []


def test_outputs_are_bounded_and_exceptions_not_retried():
    counter = []

    def fail(value):
        counter.append(value)
        raise RuntimeError("x" * 1000)

    result = make_harness([reply([call()])], fail).run(
        "Run", limits=RunLimits(max_steps=1, max_output_chars=32)
    )
    assert counter == [2]
    assert result.messages[-1]["content"].endswith("[output truncated]")
    assert len(result.messages[-1]["content"]) < 60


@pytest.mark.parametrize("content", ["not json", '{"value": "bad"}', '{"value": NaN}'])
def test_invalid_structured_output_is_not_success(content):
    result = make_harness([{"role": "assistant", "content": content}]).run(
        "Run", output_schema=SCHEMA
    )
    assert result.status == "invalid_output"
    assert result.data is None


def test_independent_histories_and_registries_under_concurrency():
    def run(value):
        harness = make_harness([reply([call()])], lambda value: value)
        result = harness.run(str(value), limits=RunLimits(max_steps=1))
        return result.messages[1]["content"], result.run_id

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, range(12)))
    assert [x[0] for x in results] == list(map(str, range(12)))
    assert len({x[1] for x in results}) == 12


def test_history_and_metadata_are_independent():
    first = make_harness([{"role": "assistant", "content": "secret output"}]).run("secret input")
    harness = make_harness([{"role": "assistant", "content": "next"}])
    second = harness.run("again", history=first.messages)
    assert len(first.messages) == 3 and len(second.messages) == 5
    assert "secret" not in json.dumps([vars(e) for e in first.events])
    second.messages[0]["content"] = "changed"
    assert first.messages[0]["content"] != "changed"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_steps": 0},
        {"max_tool_calls": -1},
        {"max_steps": True},
        {"max_time": float("nan")},
        {"max_time": 0},
        {"max_output_chars": 0},
    ],
)
def test_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        RunLimits(**kwargs)


def test_duplicate_tools_and_duplicate_call_ids_rejected_before_effects():
    tool = Tool("double", "Double", SCHEMA, lambda value: value)
    with pytest.raises(ValueError, match="unique"):
        Harness(ScriptedModel([]), model_name="offline", tools=[tool, tool])
    effects = []
    with pytest.raises(ValueError, match="unique"):
        make_harness([reply([call(), call()])], effects.append).run("Run")
    assert not effects
