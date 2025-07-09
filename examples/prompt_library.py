"""Demonstrate using the prompt library."""
from pygent import Agent, PROMPT_BUILDERS, set_system_message_builder

set_system_message_builder(PROMPT_BUILDERS["assistant"])

ag = Agent()
ag.step("echo 'Demo'")
ag.runtime.cleanup()
