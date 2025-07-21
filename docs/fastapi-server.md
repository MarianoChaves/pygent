# FastAPI Server

Pygent can expose the `TaskManager` over HTTP using FastAPI. This optional server lets you create and monitor tasks remotely, mirroring the CLI workflow.

Install the server dependencies with the `server` extra:

```bash
pip install pygent[server]
```

Start the server with `uvicorn`:

```bash
uvicorn pygent.fastapi_app:create_app
```

The API provides the following endpoints:

* `POST /tasks` – start a new task. Payload fields match the arguments of `TaskManager.start_task`.
* `GET /tasks` – list task IDs and their status.
* `GET /tasks/{task_id}` – retrieve the status of a task.
* `POST /tasks/{task_id}/message` – send a message to a finished task and get the reply.
* `GET /tasks/{task_id}/history` – fetch the conversation history for a task.

Each task runs in the background just like tasks started with the CLI or the Python API. The server stores a `TaskManager` instance in `app.state.manager` so you can access it from middleware or custom routes if needed.

For quick testing you can expose a minimal web UI by using the helper function
`create_app_with_ui`:

```bash
uvicorn pygent.fastapi_app:create_app_with_ui
```

Opening `http://127.0.0.1:8000/` then shows a basic chat page that talks to the
API.
