"""Gradio client for the FastAPI server."""

from __future__ import annotations

from typing import Optional
import time
import requests


def run_api_gui(api_url: str = "http://localhost:8000") -> None:
    """Launch a simple chat interface that talks to a running API server."""
    try:
        import gradio as gr
    except ModuleNotFoundError as exc:  # pragma: no cover - optional
        raise SystemExit(
            "Gradio is required for the GUI. Install with 'pip install pygent[ui]'"
        ) from exc

    base = api_url.rstrip("/")
    task_id: Optional[str] = None

    def _wait_for_completion(tid: str) -> None:
        while True:
            resp = requests.get(f"{base}/tasks/{tid}")
            resp.raise_for_status()
            if resp.json().get("status") != "running":
                break
            time.sleep(0.5)

    def _initial_reply(prompt: str) -> str:
        nonlocal task_id
        resp = requests.post(f"{base}/tasks", json={"prompt": prompt})
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        _wait_for_completion(task_id)
        hist = requests.get(f"{base}/tasks/{task_id}/history")
        hist.raise_for_status()
        for msg in reversed(hist.json()):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return ""

    def _send_message(message: str) -> str:
        resp = requests.post(f"{base}/tasks/{task_id}/message", json={"message": message})
        resp.raise_for_status()
        return resp.json().get("response", "")

    def _respond(message: str, history: Optional[list[tuple[str, str]]]) -> str:
        if task_id is None:
            return _initial_reply(message)
        return _send_message(message)

    try:
        gr.ChatInterface(_respond, title="Pygent API Chat").launch()
    finally:
        pass


def main() -> None:  # pragma: no cover - optional CLI
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    run_api_gui(url)

