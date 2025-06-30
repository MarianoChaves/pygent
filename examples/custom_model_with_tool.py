"""Custom model returning a tool call."""
import json
from pygent import Agent, openai_compat


class BashModel:
    """Return a bash tool call for the last user message."""

    def chat(self, messages, model, tools):
        cmd = messages[-1]["content"]
        call = openai_compat.ToolCall(
            id="1",
            type="function",
            function=openai_compat.ToolCallFunction(
                name="bash",
                arguments=json.dumps({"cmd": cmd}),
            ),
        )
        return openai_compat.Message(role="assistant", content=None, tool_calls=[call])


ag = Agent(model=BashModel())
ag.step("echo 'hi from tool'")
ag.runtime.cleanup()
