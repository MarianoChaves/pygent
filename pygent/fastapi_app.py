from __future__ import annotations

"""FastAPI server exposing the :class:`TaskManager` over HTTP."""

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .task_manager import TaskManager
from .runtime import Runtime


class _NewTask(BaseModel):
    prompt: str
    files: Optional[List[str]] = None
    persona: Optional[str] = None
    step_timeout: Optional[float] = None
    task_timeout: Optional[float] = None


class _UserMessage(BaseModel):
    message: str
    step_timeout: Optional[float] = None
    max_time: Optional[float] = None


def create_app() -> FastAPI:
    """Return a ``FastAPI`` application wrapping :class:`TaskManager`."""

    manager = TaskManager()
    runtime = Runtime()

    app = FastAPI()
    app.state.manager = manager
    app.state.runtime = runtime

    @app.post("/tasks")
    def start_task(req: _NewTask):
        tid = manager.start_task(
            req.prompt,
            runtime,
            files=req.files,
            persona=req.persona,
            step_timeout=req.step_timeout,
            task_timeout=req.task_timeout,
        )
        return {"task_id": tid}

    @app.get("/tasks")
    def list_tasks():
        return [
            {"id": tid, "status": task.status}
            for tid, task in manager.tasks.items()
        ]

    @app.get("/tasks/{task_id}")
    def task_status(task_id: str):
        if task_id not in manager.tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"id": task_id, "status": manager.status(task_id)}

    @app.post("/tasks/{task_id}/message")
    def message_task(task_id: str, req: _UserMessage):
        task = manager.tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.thread.is_alive():
            raise HTTPException(status_code=409, detail="Task is running")
        reply = task.agent.run_until_stop(
            req.message,
            step_timeout=req.step_timeout,
            max_time=req.max_time,
        )

        content = reply.content if reply else ""
        ask_user = None
        if reply and reply.tool_calls:
            import json

            for call in reply.tool_calls:
                if call.function.name == "ask_user":
                    try:
                        args = json.loads(call.function.arguments or "{}")
                    except Exception:
                        args = {}
                    ask_user = {
                        "prompt": args.get("prompt"),
                        "options": args.get("options"),
                    }
                    break

        return {"response": content, "ask_user": ask_user}

    @app.get("/tasks/{task_id}/history")
    def task_history(task_id: str):
        task = manager.tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.agent.history

    return app


def main() -> None:  # pragma: no cover - optional CLI
    import uvicorn

    uvicorn.run(create_app())

