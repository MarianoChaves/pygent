"""Exemplo simples de uso do Pygent via API."""
from pygent import Agent

ag = Agent()
ag.step("echo 'Ola Mundo'")
ag.runtime.cleanup()

