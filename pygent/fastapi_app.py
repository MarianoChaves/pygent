from __future__ import annotations

"""FastAPI server exposing the :class:`TaskManager` over HTTP."""

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

UI_HTML = """<!doctype html>
<html>
<head>
  <title>Pygent API</title>
  <style>
    body { font-family: sans-serif; max-width: 720px; margin: 2em auto; }
    #chat div { margin: .5em 0; }
  </style>
</head>
<body>
  <h1>Pygent API UI</h1>
  <div id="chat"></div>
  <form id="form">
    <input id="msg" autocomplete="off" style="width: 80%" />
    <button>Send</button>
  </form>
<script>
let taskId = null;
const chat = document.getElementById('chat');
document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const inp = document.getElementById('msg');
  const text = inp.value;
  inp.value = '';
  chat.innerHTML += `<div><b>You:</b> ${text}</div>`;
  if (!taskId) {
    const r = await fetch('/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({prompt:text})});
    const j = await r.json();
    taskId = j.task_id;
    let status;
    do {
      const s = await fetch('/tasks/' + taskId);
      status = (await s.json()).status;
      if (status === 'running') await new Promise(r => setTimeout(r, 1000));
    } while (status === 'running');
    const h = await fetch(`/tasks/${taskId}/history`);
    const hist = await h.json();
    const last = hist[hist.length - 1];
    chat.innerHTML += `<div><b>Assistant:</b> ${last.content || ''}</div>`;
  } else {
    const r = await fetch(`/tasks/${taskId}/message`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:text})});
    const j = await r.json();
    chat.innerHTML += `<div><b>Assistant:</b> ${j.response}</div>`;
  }
});
</script>
</body>
</html>"""

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


def create_app(with_ui: bool = False) -> FastAPI:
    """Return a ``FastAPI`` application wrapping :class:`TaskManager`.

    Pass ``with_ui=True`` to include a minimal browser UI at the root path.
    """

    manager = TaskManager()
    runtime = Runtime()

    app = FastAPI()
    app.state.manager = manager
    app.state.runtime = runtime

    if with_ui:
        @app.get("/", response_class=HTMLResponse)
        def _ui_root() -> str:
            return UI_HTML

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
        return {"response": content}

    @app.get("/tasks/{task_id}/history")
    def task_history(task_id: str):
        task = manager.tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.agent.history

    return app


def create_app_with_ui() -> FastAPI:
    """Convenience wrapper for ``create_app(with_ui=True)``."""

    return create_app(with_ui=True)


def main() -> None:  # pragma: no cover - optional CLI
    import uvicorn

    uvicorn.run(create_app())

