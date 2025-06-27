import os
import json
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib import request

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
    content: str | None = None
    tool_calls: List[ToolCall] | None = None

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
    with request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


class _ChatCompletions:
    def create(self, model: str, messages: List[Dict[str, Any]], tools: Any = None, tool_choice: str | None = "auto") -> ChatCompletion:
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
                tool_calls.append(ToolCall(id=tc.get("id", ""), type=tc.get("type", ""), function=func))
            msg = Message(role=msg_data.get("role", ""), content=msg_data.get("content"), tool_calls=tool_calls or None)
            choices.append(Choice(message=msg))
        return ChatCompletion(choices=choices)


class _Chat:
    def __init__(self) -> None:
        self.completions = _ChatCompletions()


chat = _Chat()
