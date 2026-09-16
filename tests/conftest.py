"""Use installed dependencies and explicitly choose local execution in unit tests."""
import openai  # noqa: F401
import rich.console  # noqa: F401
import rich.markdown  # noqa: F401
import rich.panel  # noqa: F401
import rich.syntax  # noqa: F401
import pytest

try:
    import docker  # noqa: F401
except ImportError:
    pass


@pytest.fixture(autouse=True)
def explicit_local_runtime(monkeypatch, tmp_path):
    monkeypatch.setenv("PYGENT_USE_DOCKER", "0")
    monkeypatch.setenv("PYGENT_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.setenv("PYGENT_LOG_FILE", str(tmp_path / "cli.log"))
