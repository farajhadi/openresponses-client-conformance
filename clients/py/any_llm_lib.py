"""any-llm-sdk, any_llm.responses(..., stream=True) with provider openai and a custom api_base."""
from _common import emit, guard
from any_llm import responses


def main(base):
    final = None
    for ev in responses(model="openai:fake-model", input_data="hi", stream=True, api_base=base, api_key="test-key"):
        if getattr(ev, "type", "") in ("response.completed", "response.failed", "response.incomplete"):
            final = ev.response
    if final is None:
        emit(status=None)
        return
    fc = next(({"name": o.name, "arguments": o.arguments} for o in final.output if o.type == "function_call"), None)
    emit(text=final.output_text or None, function_call=fc, status=final.status)


guard(main)
