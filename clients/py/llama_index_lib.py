"""llama-index-llms-openai, OpenAIResponses(...).stream_chat(...) as its docs show; the last chunk is the full message.\nllama-index does not expose the response status, so status-only expectations fail for it."""
from _common import emit, guard
from llama_index.llms.openai import OpenAIResponses
from llama_index.core.llms import ChatMessage


def main(base):
    llm = OpenAIResponses(model="gpt-4o", api_base=base, api_key="test-key", max_retries=0, timeout=20)
    last = None
    for ch in llm.stream_chat([ChatMessage(role="user", content="hi")]):
        last = ch
    msg = last.message
    # tool calls come back as ToolCallBlock items in message.blocks (llama-index >= 0.14)
    tcb = [b for b in msg.blocks if type(b).__name__ == "ToolCallBlock"]
    fc = {"name": tcb[0].tool_name, "arguments": tcb[0].tool_kwargs} if tcb else None
    text = "".join(b.text for b in msg.blocks if type(b).__name__ == "TextBlock")
    emit(text=text or None, function_call=fc, status=None)


guard(main)
