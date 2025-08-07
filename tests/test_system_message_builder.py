import sys
import types

sys.modules.setdefault('openai', types.ModuleType('openai'))

from pygent.agent import Agent


def test_instance_system_message_builder():
    def b(persona, disabled_tools=None):
        return f"CUSTOM:{persona.name}"

    ag = Agent(system_message_builder=b)
    assert ag.system_msg == "CUSTOM:Pygent"

    ag2 = Agent()
    assert ag2.system_msg != "CUSTOM:Pygent"
