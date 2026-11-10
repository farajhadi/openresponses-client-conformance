"""openai (Python SDK), Responses streaming helper as its README shows: client.responses.stream(...)."""
from _common import emit, guard
from openai import OpenAI


def main(base):
    client = OpenAI(base_url=base, api_key="test-key", max_retries=0, timeout=20)
    with client.responses.stream(model="fake-model", input="hi") as stream:
        for _ in stream:
            pass
        final = stream.get_final_response()
    fc = next(({"name": o.name, "arguments": o.arguments} for o in final.output if o.type == "function_call"), None)
    emit(text=final.output_text or None, function_call=fc, status=final.status)


guard(main)
