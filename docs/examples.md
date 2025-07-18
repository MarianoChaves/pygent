# Examples

This page collects small scripts demonstrating different aspects of Pygent. Each link points to the source file on GitHub.

- [api_example.py](https://github.com/marianochaves/pygent/blob/main/examples/api_example.py) &ndash; minimal use of the :class:`~pygent.agent.Agent` API.
- [runtime_example.py](https://github.com/marianochaves/pygent/blob/main/examples/runtime_example.py) &ndash; using the :class:`~pygent.runtime.Runtime` class directly.
- [write_file_demo.py](https://github.com/marianochaves/pygent/blob/main/examples/write_file_demo.py) &ndash; calling the built-in tools from Python code.
- [custom_model.py](https://github.com/marianochaves/pygent/blob/main/examples/custom_model.py) &ndash; implementing a simple custom model.
- [custom_model_with_tool.py](https://github.com/marianochaves/pygent/blob/main/examples/custom_model_with_tool.py) &ndash; custom model issuing tool calls.
- [custom_tool.py](https://github.com/marianochaves/pygent/blob/main/examples/custom_tool.py) &ndash; registering a custom tool.
- [delegate_task_example.py](https://github.com/marianochaves/pygent/blob/main/examples/delegate_task_example.py) &ndash; delegating work to a background agent.
- [config_file_example.py](https://github.com/marianochaves/pygent/blob/main/examples/config_file_example.py) &ndash; loading a config file and delegating a testing agent.
- [delegate_external_tool.py](https://github.com/marianochaves/pygent/blob/main/examples/delegate_external_tool.py) &ndash; new tool using an external model service inside a delegated task.
- [crew_example.py](https://github.com/marianochaves/pygent/blob/main/examples/crew_example.py) &ndash; coordenando dois agentes em paralelo.
- [prompt_library.py](https://github.com/marianochaves/pygent/blob/main/examples/prompt_library.py) &ndash; using the prebuilt system message builders.
- [agent_presets.py](https://github.com/marianochaves/pygent/blob/main/examples/agent_presets.py) &ndash; launching an agent from a preset.

See the [Custom Models](custom-models.md) page for a walkthrough of building your own models.

Run these with `python <script>` from the project root. They expect the environment variables described in the [Configuration](configuration.md) page.
