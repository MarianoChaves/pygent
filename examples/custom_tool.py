"""Demonstrate registering and using a custom tool."""
from pygent import Agent, register_tool


def hello(rt, name: str) -> str:
    return f"Hello {name}!"

register_tool(
    "hello",
    "Greet by name",
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    hello,
)

ag = Agent()
ag.step("hello name='world'")
ag.runtime.cleanup()
