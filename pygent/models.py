from __future__ import annotations

"""Model interface and default implementation for OpenAI-compatible APIs."""

from typing import Any, Dict, List, Protocol

try:
    import openai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback to bundled client
    from . import openai_compat as openai

from .openai_compat import Message
from .errors import APIError


class Model(Protocol):
    """Protocol for chat models used by :class:`~pygent.agent.Agent`."""

    def chat(self, messages: List[Dict[str, Any]], model: str, tools: Any) -> Message:
        """Return the assistant message for the given prompt."""
        ...


class OpenAIModel:
    """Default model using the OpenAI-compatible API."""

    def chat(self, messages: List[Dict[str, Any]], model: str, tools: Any) -> Message:
        try:
            resp = openai.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            return resp.choices[0].message
        except Exception as exc:
            raise APIError(str(exc)) from exc
