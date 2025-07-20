import os
import sys
import types

import pytest

pytest.importorskip("fastapi")

sys.modules.setdefault("openai", types.ModuleType("openai"))
sys.modules.setdefault("docker", types.ModuleType("docker"))

from fastapi.testclient import TestClient
from pygent.fastapi_app import create_app


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_web_ui_served():
    app = create_app(include_ui=True)
    client = TestClient(app)
    resp = client.get("/ui/index.html")
    assert resp.status_code == 200
    assert "Pygent API Web UI" in resp.text
