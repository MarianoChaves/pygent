"""Approve a workspace write explicitly; no shell commands or network calls."""

from tempfile import TemporaryDirectory

from pygent import Harness, Tool
from pygent.runtime import Runtime
from pygent.testing import ScriptedModel


def main():
    with (
        TemporaryDirectory() as directory,
        Runtime(use_docker=False, workspace=directory) as runtime,
    ):
        model = ScriptedModel(
            [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "write-1",
                            "type": "function",
                            "function": {
                                "name": "write_file",
                                "arguments": '{"path": "hello.txt", "content": "Hello from Pygent!"}',
                            },
                        }
                    ],
                },
                {"role": "assistant", "content": "Created hello.txt."},
            ]
        )
        write = Tool(
            "write_file",
            "Write a UTF-8 workspace file.",
            {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            runtime.write_file,
            requires_approval=True,
        )
        result = Harness(model, model_name="offline", tools=[write]).run(
            "Create a greeting file.",
            approve=lambda name, args: name == "write_file" and args["path"] == "hello.txt",
        )
        assert result.status == "completed"
        assert runtime.read_file("hello.txt") == "Hello from Pygent!"
        print(result.output)


if __name__ == "__main__":
    main()
