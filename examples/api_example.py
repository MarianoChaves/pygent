"""Simple example of using Pygent via the API.

The agent expects an OpenAI-compatible backend. Set the
``OPENAI_API_KEY`` environment variable to your API key. To use a
provider other than OpenAI, also set ``OPENAI_BASE_URL`` with the
provider's endpoint.
"""

import os
from pygent import Agent

# Uncomment and fill in your credentials:
# os.environ["OPENAI_API_KEY"] = "sk-..."
# os.environ["OPENAI_BASE_URL"] = "https://other-provider.example.com/v1"

ag = Agent()
ag.step("echo 'Hello World'")
ag.runtime.cleanup()

