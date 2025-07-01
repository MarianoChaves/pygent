# Custom Models

Pygent allows plugging in any model backend as long as it implements the `Model` protocol. This page collects extended examples showing how to build your own models, use the `openai_compat` helpers and return tool calls.

## Echo model

A trivial example that simply repeats the last user message. The implementation returns an `openai_compat.Message` instance.

```python
from pygent import Agent, openai_compat

class EchoModel:
    def chat(self, messages, model, tools):
        last = messages[-1]["content"]
        return openai_compat.Message(role="assistant", content=f"Echo: {last}")

ag = Agent(model=EchoModel())
ag.step("test")
```

## Calling a remote API with `openai_compat`

The `openai_compat` module ships a lightweight client mirroring the official OpenAI interface. You can use it to talk to any compatible endpoint.

```python
from pygent import Agent, openai_compat

class HTTPModel:
    def chat(self, messages, model, tools):
        resp = openai_compat.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        return resp.choices[0].message

ag = Agent(model=HTTPModel())
ag.step("who am I?")
```

Set `OPENAI_BASE_URL` and `OPENAI_API_KEY` to target a different provider if needed.

## Returning tool calls

Custom models may trigger tools by returning a message with the `tool_calls` attribute populated. The next example runs the last user message as a `bash` command.

```python
import json
from pygent import Agent, openai_compat

class BashModel:
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
```

## Global custom model

Use `set_custom_model` to apply a model to all new agents and delegated tasks:

```python
from pygent import Agent
from pygent.models import set_custom_model

set_custom_model(EchoModel())
ag = Agent()
ag.step("hello")
set_custom_model(None)
```

## Delegating tasks from a custom model

Models can call the `delegate_task` tool to start a background agent. This example delegates once and then stops.

```python
import json
from pygent import Agent, openai_compat

class DelegateModel:
    def __init__(self):
        self.first = True

    def chat(self, messages, model, tools):
        if self.first:
            self.first = False
            return openai_compat.Message(
                role="assistant",
                content=None,
                tool_calls=[
                    openai_compat.ToolCall(
                        id="1",
                        type="function",
                        function=openai_compat.ToolCallFunction(
                            name="delegate_task",
                            arguments=json.dumps({"prompt": "noop"}),
                        ),
                    )
                ],
            )
        return openai_compat.Message(role="assistant", content=None, tool_calls=[
            openai_compat.ToolCall(
                id="2",
                type="function",
                function=openai_compat.ToolCallFunction(name="stop", arguments="{}"),
            )
        ])

ag = Agent(model=DelegateModel())
ag.run_until_stop("begin", max_steps=2)
```

These snippets demonstrate different ways of integrating custom logic with Pygent. See the [examples](examples.md) directory for the full source code.
