class PygentError(Exception):
    """Base error for the Pygent package."""


class APIError(PygentError):
    """Raised when the OpenAI API call fails."""
