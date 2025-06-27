"""Map of tools available to the agent."""
from __future__ import annotations
import json
from typing import Any, Dict

from .runtime import Runtime

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command inside the sandboxed container.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Command to execute"}
                },
                "required": ["cmd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
]

# --------------- dispatcher ---------------

def execute_tool(call: Any, rt: Runtime) -> str:  # pragma: no cover, Any→openai.types.ToolCall
    name = call.function.name
    args: Dict[str, Any] = json.loads(call.function.arguments)

    if name == "bash":
        return rt.bash(**args)
    if name == "write_file":
        return rt.write_file(**args)
    return f"⚠️ unknown tool {name}"
