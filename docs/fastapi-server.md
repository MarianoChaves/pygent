# FastAPI Server (Legacy)

> Legacy note: HTTP task orchestration is optional and outside the default CLI-first flow.

If you still need server mode:

```bash
pip install pygent[server]
uvicorn pygent.fastapi_app:create_app
```

The server exposes task endpoints backed by `TaskManager`.
See `docs/openapi.yaml` for a reference schema.
