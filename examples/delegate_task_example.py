"""Demonstrate delegating a task to a sub-agent."""
import time
from pygent import TaskManager, Runtime

manager = TaskManager()
tid = manager.start_task("write_file path='hello.txt' content='hi'\nstop")
print("Started", tid)
while manager.status(tid) == "running":
    time.sleep(1)
print("Status:", manager.status(tid))
rt = Runtime(use_docker=False)
print(manager.collect_file(rt, tid, "hello.txt"))
rt.cleanup()
