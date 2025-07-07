# Custom System Message

Pygent builds the initial system prompt dynamically based on the persona
and the currently active tools. If you want full control over this
message you can supply your own builder function.

Use `set_system_message_builder` to register a callable that returns the
system prompt. A convenient place to do this is in a `config.py` file
loaded on start-up.

```python
# config.py
from pygent.agent import set_system_message_builder


def my_system_builder(persona, disabled_tools=None):
    return f"{persona.name}: ready to work"

set_system_message_builder(my_system_builder)
```

Pass `None` to `set_system_message_builder` to restore the default
prompt generation logic.
