"""langchain-openai, ChatOpenAI(use_responses_api=True).stream(...): chunks are added together, as its docs show."""
import json
from _common import emit, guard
from langchain_openai import ChatOpenAI


def main(base):
    llm = ChatOpenAI(model="fake-model", base_url=base, api_key="test-key", use_responses_api=True, max_retries=0,
                     timeout=20, streaming=True)
    full = None
    for ch in llm.stream("hi"):
        full = ch if full is None else full + ch
    text = full.text if isinstance(full.text, str) else full.text()
    fc = None
    if full.tool_calls:
        tc = full.tool_calls[0]
        fc = {"name": tc["name"], "arguments": json.dumps(tc["args"], ensure_ascii=False)}
    elif getattr(full, "invalid_tool_calls", None):
        tc = full.invalid_tool_calls[0]
        fc = {"name": tc["name"], "arguments": tc["args"]}
    status = (full.response_metadata or {}).get("status")
    emit(text=text or None, function_call=fc, status=status)


guard(main)
