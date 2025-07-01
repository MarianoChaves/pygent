"""Delegate a task that uses a custom tool and an external model service."""
import json
import time
from pygent import Agent, TaskManager, register_tool, Runtime, openai_compat


def shout(rt: Runtime, text: str) -> str:
    """Return the given text in uppercase."""
    return text.upper()


register_tool(
    "shout",
    "Uppercase some text",
    {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    shout,
)


class HTTPModel:
    """Proxy requests to an OpenAI-compatible endpoint."""

    def chat(self, messages, model, tools):
        resp = openai_compat.chat.completions.create(
            model=model, messages=messages, tools=tools, tool_choice="auto"
        )
        return resp.choices[0].message


class DelegatingModel:
    """Delegate once and stop."""

    def __init__(self):
        self.done = False

    def chat(self, messages, model, tools):
        if not self.done:
            self.done = True
            return openai_compat.Message(
                role="assistant",
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id="1",
                        type="function",
                        function=openai_compat.ToolCallFunction(
                            name="delegate_task",
                            arguments=json.dumps({"prompt": "shout text='hello'\nstop"}),
                        ),
                    )
                ],
            )
        return openai_compat.Message(role="assistant", content="delegated")


manager = TaskManager(agent_factory=lambda p=None: Agent(model=HTTPModel(), persona=p))
main = Agent(model=DelegatingModel())

# Launch the delegated task using the custom tool and external model
task_id = manager.start_task("begin", main.runtime)
print("Started", task_id)

while manager.status(task_id) == "running":
    time.sleep(1)

print("Status:", manager.status(task_id))
main.runtime.cleanup()
