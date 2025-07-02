"""Simple Gradio-based chat interface."""

from .agent import Agent
from .runtime import Runtime
from .tools import execute_tool, TOOL_SCHEMAS
from . import openai_compat


from typing import Optional


def run_gui(use_docker: Optional[bool] = None) -> None:
    """Launch a simple Gradio chat interface."""
    try:
        import gradio as gr
    except ModuleNotFoundError as exc:  # pragma: no cover - optional
        raise SystemExit(
            "Gradio is required for the GUI. Install with 'pip install pygent[ui]'"
        ) from exc

    agent = Agent(runtime=Runtime(use_docker=use_docker))

    def _respond(message: str, history: Optional[list[tuple[str, str]]]) -> str:
        agent.append_history({"role": "user", "content": message})
        raw = agent.model.chat(agent.history, agent.model_name, TOOL_SCHEMAS)
        assistant_msg = openai_compat.parse_message(raw)
        agent.append_history(assistant_msg)
        reply = assistant_msg.content or ""
        if assistant_msg.tool_calls:
            for call in assistant_msg.tool_calls:
                output = execute_tool(call, agent.runtime)
                agent.append_history(
                    {"role": "tool", "content": output, "tool_call_id": call.id}
                )
                reply += f"\n\n[tool:{call.function.name}]\n{output}"
        return reply

    try:
        gr.ChatInterface(_respond, title="Pygent").launch()
    finally:
        agent.runtime.cleanup()


def main() -> None:  # pragma: no cover
    run_gui()
