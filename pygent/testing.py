"""Deterministic models for tests, examples and offline harness evaluation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Sequence

from .openai_compat import Message, parse_message


class ScriptedModel:
    """Return each supplied response once; fail if the script is exhausted.

    Create one instance per concurrent run. Recorded requests are independent
    copies, so tests can assert tool schemas and transcript protocol details.
    """

    def __init__(self, responses: Sequence[Message | dict[str, Any]]) -> None:
        self._responses = deepcopy(list(responses))
        self.requests: list[dict[str, Any]] = []

    def chat(self, messages: list[dict[str, Any]], model: str, tools: Any) -> Message:
        index = len(self.requests)
        if index >= len(self._responses):
            raise RuntimeError("ScriptedModel responses exhausted")
        self.requests.append(deepcopy({"messages": messages, "model": model, "tools": tools}))
        return parse_message(deepcopy(self._responses[index]))
