"""Run the FastAPI server with the built-in web interface."""

from .fastapi_app import create_app


app = create_app(include_ui=True)


def main() -> None:  # pragma: no cover - optional CLI
    import uvicorn
    uvicorn.run(app)
