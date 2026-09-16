from __future__ import annotations

"""Model interface and default implementation for OpenAI-compatible APIs."""

from typing import Any, Dict, List, Protocol, Optional
from dataclasses import asdict, is_dataclass

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

    def __init__(self, client: Any = None) -> None:
        """Optionally inject a configured client (credentials, timeout and retries)."""
        self.client = client

    def chat(self, messages: List[Dict[str, Any]], model: str, tools: Any) -> Message:
        try:
            serialized = [
                asdict(m) if is_dataclass(m) else m
                for m in messages
            ]
            kwargs = {"model": model, "messages": serialized}
            if tools:
                kwargs.update(tools=tools, tool_choice="auto")
            client = self.client if self.client is not None else openai
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message
        except Exception as exc:
            raise APIError(str(exc)) from exc


# global custom model used for all new agents when set
CUSTOM_MODEL: Optional[Model] = None


def set_custom_model(model: Optional[Model]) -> None:
    """Set a global custom model used by :class:`~pygent.agent.Agent`."""

    global CUSTOM_MODEL
    CUSTOM_MODEL = model
