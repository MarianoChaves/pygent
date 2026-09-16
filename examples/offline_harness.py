"""Run a real tool with a scripted model, without network, Docker or API keys."""

from pygent import Harness, RunLimits, Tool
from pygent.testing import ScriptedModel


def main():
    model = ScriptedModel(
        [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "check-1",
                        "type": "function",
                        "function": {"name": "add", "arguments": '{"a": 2, "b": 3}'},
                    }
                ],
            },
            {"role": "assistant", "content": "The result is 5."},
        ]
    )
    add = Tool(
        "add",
        "Add two integers.",
        {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        lambda a, b: a + b,
    )
    result = Harness(model, model_name="offline", tools=[add]).run(
        "What is 2 + 3?", limits=RunLimits(max_steps=3)
    )
    assert result.status == "completed"
    assert result.messages[-2]["content"] == "5"
    print(result.output)


if __name__ == "__main__":
    main()
