"""Demonstrate using bash and write_file tools through the API."""
from pygent import Agent

ag = Agent()
ag.step("write_file path='hello.txt' content='Hello from Pygent'")
ag.step("bash cmd='cat hello.txt'")
ag.runtime.cleanup()
