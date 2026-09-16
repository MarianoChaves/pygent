from types import SimpleNamespace

from pygent.models import OpenAIModel


def test_injected_client_omits_empty_tools_and_preserves_tool_responses():
    requests = []

    def create(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message={"role": "assistant", "content": "ok"})]
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    model = OpenAIModel(client=client)
    history = [{"role": "tool", "tool_call_id": "one", "content": "result"}]
    assert model.chat(history, "configured-model", []) == {"role": "assistant", "content": "ok"}
    assert requests[0] == {"model": "configured-model", "messages": history}
