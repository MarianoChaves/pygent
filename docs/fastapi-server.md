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

## Simple Web Interface

You can interact with the API server through a minimal Gradio front-end. Install
the optional UI dependencies and run:

```bash
pip install pygent[ui]
pygent-api-ui
```

By default the interface expects the server at `http://localhost:8000`. Pass a
different URL as the first argument if needed:

```bash
pygent-api-ui http://your-server:8000
```

The page lets you chat with the running API server just like the CLI.
