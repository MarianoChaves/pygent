"""Lightweight client compatible with the OpenAI HTTP API."""

import os
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib import request, error

from .errors import APIError

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


@dataclass
class ToolCallFunction:
    name: str
    arguments: str


@dataclass
class ToolCall:
    id: str
    type: str
    function: ToolCallFunction


@dataclass
class Message:
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


@dataclass
class Choice:
    message: Message


@dataclass
class ChatCompletion:
    choices: List[Choice]


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    req = request.Request(f"{OPENAI_BASE_URL}{path}", data=data, headers=headers)
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except error.HTTPError as exc:  # pragma: no cover - network dependent
        raise APIError(f"HTTP error {exc.code}: {exc.reason}") from exc
    except error.URLError as exc:  # pragma: no cover - network dependent
        raise APIError(f"Connection error: {exc.reason}") from exc
    except Exception as exc:  # pragma: no cover - fallback
        raise APIError(str(exc)) from exc


class _ChatCompletions:
    def create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Any = None,
        tool_choice: Optional[str] = "auto",
    ) -> ChatCompletion:
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        raw = _post("/chat/completions", payload)
        choices: List[Choice] = []
        for ch in raw.get("choices", []):
            msg_data = ch.get("message", {})
            tool_calls = []
            for tc in msg_data.get("tool_calls", []):
                func = ToolCallFunction(**tc.get("function", {}))
                tool_calls.append(
                    ToolCall(
                        id=tc.get("id", ""), type=tc.get("type", ""), function=func
                    )
                )
            msg = Message(
                role=msg_data.get("role", ""),
                content=msg_data.get("content"),
                tool_calls=tool_calls or None,
            )
            choices.append(Choice(message=msg))
        return ChatCompletion(choices=choices)


class _Chat:
    def __init__(self) -> None:
        self.completions = _ChatCompletions()


chat = _Chat()


def parse_message(raw: Any) -> Message:
    """Return a :class:`Message` from ``raw`` data.

    Accepts dictionaries and objects from the official OpenAI client.
    """
    if isinstance(raw, Message):
        return raw
    if isinstance(raw, dict):
        tool_calls = []
        for tc in raw.get("tool_calls", []) or []:
            func_data = tc.get("function", {})
            func = ToolCallFunction(
                name=func_data.get("name", ""),
                arguments=func_data.get("arguments", ""),
            )
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", ""),
                    type=tc.get("type", ""),
                    function=func,
                )
            )
        return Message(
            role=raw.get("role", ""),
            content=raw.get("content"),
            tool_calls=tool_calls or None,
        )
    if hasattr(raw, "model_dump"):
        return parse_message(raw.model_dump())
    if hasattr(raw, "to_dict"):
        return parse_message(raw.to_dict())
    raise TypeError(f"Unsupported message type: {type(raw)!r}")
