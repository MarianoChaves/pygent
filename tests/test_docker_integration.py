"""Real daemon tests, enabled explicitly in the dedicated CI job."""

import os
import time

import pytest

from pygent.runtime import Runtime

pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(
        os.getenv("PYGENT_TEST_DOCKER") != "1",
        reason="set PYGENT_TEST_DOCKER=1 for real Docker tests",
    ),
]


def test_real_docker_shell_timeout_and_workspace(tmp_path):
    with Runtime(use_docker=True, workspace=tmp_path) as runtime:
        assert runtime.use_docker
        output = runtime.bash("printf hello | cat > result.txt; cat result.txt", timeout=5)
        assert output.endswith("hello")
        assert runtime.read_file("result.txt") == "hello"
        start = time.monotonic()
        runtime.bash("sleep 20", timeout=0.1)
        assert time.monotonic() - start < 5
        chunks = []
        output = runtime.bash("printf streamed", stream=chunks.append)
        assert output.endswith("streamed")
        assert "".join(chunks) == output
