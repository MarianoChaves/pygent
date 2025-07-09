"""Launch an agent using one of the predefined presets."""
from pygent import AGENT_PRESETS

ag = AGENT_PRESETS["autonomous"].create_agent()
ag.run_until_stop("echo 'Preset demo'")
ag.runtime.cleanup()

