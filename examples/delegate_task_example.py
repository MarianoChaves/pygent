"""Demonstrate delegating a task to a sub-agent."""
import time
from pygent import TaskManager, Runtime

manager = TaskManager()
main_rt = Runtime(use_docker=False)
main_rt.write_file("msg.txt", "hi")
tid = manager.start_task(
    "bash cmd='cat msg.txt'\nwrite_file path='hello.txt' content='done'\nstop",
    main_rt,
    files=["msg.txt"],
)
print("Started", tid)
while manager.status(tid) == "running":
    time.sleep(1)
print("Status:", manager.status(tid))
print(manager.collect_file(main_rt, tid, "hello.txt"))
main_rt.cleanup()
