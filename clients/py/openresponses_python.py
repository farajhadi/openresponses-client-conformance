"""openresponses-python (PyPI, "un-official SDK"). Its stream yields raw events (event name + data dict) and gives no
final-response helper, so the adapter does the minimum a user must: join output_text deltas and function-call
argument deltas, and read the status from the terminal event. Its base_url excludes /v1 (it appends /v1/responses)."""
from _common import emit, guard
from openresponses.client import OpenResponsesClient


def main(base):
    client = OpenResponsesClient(base_url=base[: -len("/v1")], api_key="test-key")
    text, args, name, status = "", "", None, None
    for ev in client.create(model="fake-model", input="hi", stream=True):
        d = ev.data if isinstance(ev.data, dict) else {}
        t = d.get("type", ev.event)
        if t == "response.output_text.delta":
            text += d["delta"]
        elif t == "response.output_item.added" and d.get("item", {}).get("type") == "function_call":
            name = d["item"]["name"]
        elif t == "response.function_call_arguments.delta":
            args += d["delta"]
        elif t in ("response.completed", "response.failed", "response.incomplete"):
            status = d["response"]["status"]
    if status is None:
        raise_ = "stream ended with no terminal event (adapter-detected, library raised nothing)"
        emit(text=text or None, function_call={"name": name, "arguments": args} if name else None, status=None)
        return
    emit(text=text or None, function_call={"name": name, "arguments": args} if name else None, status=status)


guard(main)
