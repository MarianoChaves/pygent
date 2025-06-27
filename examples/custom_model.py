"""Example of using a custom model with Pygent."""

from pygent import Agent, openai_compat


class EchoModel:
    """A trivial model that echoes the last user message."""

    def chat(self, messages, model, tools):
        last = messages[-1]["content"]
        return openai_compat.Message(role="assistant", content=f"Echo: {last}")


ag = Agent(model=EchoModel())
ag.step("test")
ag.runtime.cleanup()
