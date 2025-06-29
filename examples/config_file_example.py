"""Use a config file and delegate unit test generation."""
from pathlib import Path
import time
from pygent import Agent, load_config, TaskManager

base = Path(__file__).resolve().parent
load_config(base / "sample_config.toml")

main = Agent()
manager = TaskManager()

# Create a small Python module
main.step("write_file path='calc.py' content='def add(a, b): return a + b'")

# Launch a sub-agent that writes tests for the module
task_id = manager.start_task(
    "Write pytest tests for calc.py in test_calc.py and stop", main.runtime, files=["calc.py"]
)
print("Started", task_id)

while manager.status(task_id) == "running":
    time.sleep(1)

print("Status:", manager.status(task_id))
print(manager.collect_file(main.runtime, task_id, "test_calc.py"))

main.runtime.cleanup()
