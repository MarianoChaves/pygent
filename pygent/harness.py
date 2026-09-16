"""Small, synchronous, provider-neutral agent loop without terminal side effects.

Tools are explicitly supplied per harness. Runs own their transcript and counters;
model clients, tool functions and event sinks must support the application's chosen
concurrency model. Time limits and cancellation are cooperative between calls.
"""

from __future__ import annotations

import json
import math
import time
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from threading import Event
from typing import Any, Callable, Literal, Mapping, Sequence

from jsonschema import Draft202012Validator, ValidationError

from .models import Model
from .openai_compat import Message, parse_message

Status = Literal[
    "completed", "max_steps", "max_tool_calls", "timeout", "cancelled", "invalid_output"
]


@dataclass(frozen=True)
class RunLimits:
    """Per-run bounds. ``max_time`` is checked between blocking calls."""

    max_steps: int = 20
    max_tool_calls: int = 100
    max_output_chars: int = 16_000
    max_time: float | None = None

    def __post_init__(self) -> None:
        for name in ("max_steps", "max_tool_calls", "max_output_chars"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.max_time is not None and (not math.isfinite(self.max_time) or self.max_time <= 0):
            raise ValueError("max_time must be finite and positive")


@dataclass(frozen=True)
class Tool:
    """A named callable and its JSON Schema; no implicit global registration.

    ``function`` receives validated keyword arguments. It must return a string or
    JSON-serializable value. Set ``requires_approval`` for side-effecting actions;
    these are denied unless a run's approval callback returns exactly ``True``.
    """

    name: str
    description: str
    parameters: Mapping[str, Any]
    function: Callable[..., Any]
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.name or not callable(self.function):
            raise ValueError("tool needs a nonempty name and a callable")
        schema = deepcopy(dict(self.parameters))
        Draft202012Validator.check_schema(schema)
        if schema.get("type") != "object":
            raise ValueError("tool parameters must have type 'object'")
        object.__setattr__(self, "parameters", schema)

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": deepcopy(dict(self.parameters)),
            },
        }


@dataclass(frozen=True)
class RunEvent:
    """Metadata-only event, suitable for an application's telemetry adapter."""

    run_id: str
    kind: str
    step: int
    elapsed: float
    tool_name: str | None = None
    tool_call_id: str | None = None
    outcome: str | None = None


@dataclass
class RunResult:
    """Serializable result; only ``completed`` denotes successful completion."""

    run_id: str
    status: Status
    output: str | None
    messages: list[dict[str, Any]]
    steps: int
    tool_calls: int
    elapsed: float
    data: Any = None
    events: list[RunEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-serializable representation."""
        return asdict(self)


class Harness:
    """Run a chat model with explicit tools, limits and optional approvals.

    No runtime is created automatically. Pass bound ``Runtime`` methods as tools
    when filesystem or shell access is intended. Exceptions from models, approval
    callbacks or event sinks propagate; tools' ordinary exceptions become tool
    error messages. Tools are never automatically retried.
    """

    def __init__(
        self,
        model: Model,
        *,
        model_name: str,
        tools: Sequence[Tool] = (),
        system_prompt: str = "Complete the task using the provided tools. Reply when finished.",
    ) -> None:
        if len({tool.name for tool in tools}) != len(tools):
            raise ValueError("tool names must be unique")
        self.model = model
        self.model_name = model_name
        self.system_prompt = system_prompt
        # Copy schema metadata, retaining only the caller's actual function objects.
        self._tools = {
            tool.name: Tool(
                tool.name, tool.description, tool.parameters, tool.function, tool.requires_approval
            )
            for tool in tools
        }

    def run(
        self,
        prompt: str,
        *,
        limits: RunLimits | None = None,
        history: Sequence[dict[str, Any]] = (),
        approve: Callable[[str, dict[str, Any]], bool] | None = None,
        cancel: Event | None = None,
        on_event: Callable[[RunEvent], None] | None = None,
        output_schema: Mapping[str, Any] | None = None,
    ) -> RunResult:
        """Execute until a final answer or a bound is reached.

        ``history`` is a trusted complete transcript, e.g. ``result.messages``.
        A whole tool batch is rejected if it would exceed the tool-call budget.
        Cancelled/skipped calls receive matching tool responses so the transcript
        can be continued. Event metadata excludes prompts, arguments and outputs.
        """
        limits = limits or RunLimits()
        validator = None
        if output_schema is not None:
            Draft202012Validator.check_schema(output_schema)
            validator = Draft202012Validator(deepcopy(dict(output_schema)))
        run_id, start = uuid.uuid4().hex, time.monotonic()
        messages = deepcopy(list(history))
        if not messages:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})
        steps = calls_used = 0
        events: list[RunEvent] = []
        last: Message | None = None

        def emit(kind: str, **kwargs: Any) -> None:
            event = RunEvent(run_id, kind, steps, time.monotonic() - start, **kwargs)
            events.append(event)
            if on_event:
                on_event(event)

        def stopped() -> Status | None:
            if cancel is not None and cancel.is_set():
                return "cancelled"
            if limits.max_time is not None and time.monotonic() - start >= limits.max_time:
                return "timeout"
            return None

        def finish(status: Status, data: Any = None) -> RunResult:
            emit("run_finished", outcome=status)
            return RunResult(
                run_id,
                status,
                last.content if last else None,
                messages,
                steps,
                calls_used,
                time.monotonic() - start,
                data,
                events,
            )

        emit("run_started")
        for _ in range(limits.max_steps):
            reason = stopped()
            if reason:
                return finish(reason)
            steps += 1
            emit("model_started")
            last = parse_message(
                self.model.chat(
                    deepcopy(messages),
                    self.model_name,
                    [tool.schema() for tool in self._tools.values()],
                )
            )
            if last.role != "assistant":
                raise ValueError("model must return an assistant message")
            calls = last.tool_calls or []
            if any(not call.id for call in calls) or len({c.id for c in calls}) != len(calls):
                raise ValueError("tool call IDs must be nonempty and unique within a batch")
            message: dict[str, Any] = {"role": last.role, "content": last.content}
            if calls:
                message["tool_calls"] = [asdict(call) for call in calls]
            messages.append(message)
            emit("model_finished")
            reason = stopped()
            if not calls:
                if reason:
                    return finish(reason)
                if validator is not None:
                    try:
                        data = json.loads(last.content or "", parse_constant=_reject_constant)
                        validator.validate(data)
                    except (ValueError, ValidationError):
                        return finish("invalid_output")
                    return finish("completed", data)
                return finish("completed")
            if calls_used + len(calls) > limits.max_tool_calls:
                reason = reason or "max_tool_calls"
            for call in calls:
                reason = reason or stopped()
                name = call.function.name
                outcome = "skipped"
                if reason:
                    output = f"[error] tool not executed: {reason}"
                else:
                    calls_used += 1
                    tool = self._tools.get(name)
                    outcome = "error"
                    try:
                        if tool is None:
                            raise ValueError(f"unknown tool: {name}")
                        args = json.loads(
                            call.function.arguments or "{}", parse_constant=_reject_constant
                        )
                        Draft202012Validator(tool.parameters).validate(args)
                    except (ValueError, TypeError, ValidationError) as exc:
                        output = f"[error] invalid tool call: {exc}"
                    else:
                        if tool.requires_approval and (
                            approve is None or approve(name, deepcopy(args)) is not True
                        ):
                            output, outcome = "[error] tool execution denied", "denied"
                        elif stopped():
                            reason = stopped()
                            output = f"[error] tool not executed: {reason}"
                            outcome = "skipped"
                        else:
                            emit("tool_started", tool_name=name, tool_call_id=call.id)
                            try:
                                value = tool.function(**args)
                                output = (
                                    value
                                    if isinstance(value, str)
                                    else json.dumps(value, allow_nan=False)
                                )
                                outcome = "success"
                            except Exception as exc:
                                output = f"[error] tool failed: {type(exc).__name__}: {exc}"
                if len(output) > limits.max_output_chars:
                    output = output[: limits.max_output_chars] + "\n[output truncated]"
                messages.append({"role": "tool", "tool_call_id": call.id, "content": output})
                emit("tool_finished", tool_name=name, tool_call_id=call.id, outcome=outcome)
            reason = reason or stopped()
            if reason:
                return finish(reason)
        return finish("max_steps")


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")
