"""litellm, litellm.responses(..., stream=True) as its docs show, provider openai with a custom api_base. Model name gpt-4o: with an unknown name litellm asks for a non-streamed reply and fakes the stream, which would not test its stream parser.
litellm yields events; the final response comes from the response.completed/failed/incomplete event."""
import os
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"  # no network fetch of the price list at import
from _common import emit, guard
import litellm


def main(base):
    stream = litellm.responses(model="openai/gpt-4o", input="hi", stream=True, api_base=base, api_key="test-key",
                               num_retries=0, timeout=20)
    final = None
    for ev in stream:
        if getattr(ev, "type", "") in ("response.completed", "response.failed", "response.incomplete"):
            final = ev.response
    if final is None:
        emit(status=None)
        return
    out = final.output or []
    text = "".join(c.text for o in out if getattr(o, "type", None) == "message" for c in (o.content or [])
                   if getattr(c, "type", None) == "output_text") or None
    fc = next(({"name": o.name, "arguments": o.arguments} for o in out if getattr(o, "type", None) == "function_call"), None)
    emit(text=text, function_call=fc, status=str(final.status))


guard(main)
