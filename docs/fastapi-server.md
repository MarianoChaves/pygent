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
* `POST /tasks/{task_id}/message` – send a message to a finished task and get the reply. The response includes an optional `ask_user` field when the agent requires user input.
* `GET /tasks/{task_id}/history` – fetch the conversation history for a task.

You can view the full OpenAPI specification in your browser when the server is running at `/docs` or `/openapi.json`. The generated spec is also included in this repository as [`openapi.yaml`](openapi.yaml) for reference.

Each task runs in the background just like tasks started with the CLI or the Python API. The server stores a `TaskManager` instance in `app.state.manager` so you can access it from middleware or custom routes if needed.
