# Custom Models

Any object that implements `chat(messages, model, tools)` can be used as a model.

## Echo model

```python
from pygent import Agent, openai_compat

class EchoModel:
    def chat(self, messages, model, tools):
        last = messages[-1]["content"]
        return openai_compat.Message(role="assistant", content=f"Echo: {last}")

ag = Agent(model=EchoModel())
ag.step("test")
```

## Calling OpenAI-compatible APIs

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

## Returning tool calls

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
```

## Global model override

```python
from pygent import Agent
from pygent.models import set_custom_model

set_custom_model(EchoModel())
ag = Agent()
ag.step("hello")
set_custom_model(None)
```

## Optional legacy delegated-task usage

If you explicitly enable task tools, a custom model can call `delegate_task`.
This is now considered an advanced legacy flow and is no longer the default direction.
