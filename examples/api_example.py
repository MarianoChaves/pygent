"""Simple example of using Pygent via the API."""
from pygent import Agent

ag = Agent()
ag.step("echo 'Hello World'")
ag.runtime.cleanup()

