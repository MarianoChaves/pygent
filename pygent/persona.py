from dataclasses import dataclass

@dataclass
class Persona:
    """Simple container for a persona name and description."""
    name: str
    description: str

