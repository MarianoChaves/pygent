"""Run a custom command inside the sandboxed Runtime."""
from pygent import runtime

rt = runtime.Runtime(image="python:3.11-slim")
print(rt.bash("python --version"))
rt.cleanup()
