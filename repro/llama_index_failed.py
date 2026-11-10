"""llama-index OpenAIResponses.stream_chat on a stream that ends in response.failed. Prints everything the
library hands back, so it's visible whether any error or status reaches the caller."""
import sys
from llama_index.llms.openai import OpenAIResponses
from llama_index.core.llms import ChatMessage

port = sys.argv[1] if len(sys.argv) > 1 else "8765"
for case in ("response_failed", "response_incomplete"):
    llm = OpenAIResponses(model="gpt-4o", api_base=f"http://127.0.0.1:{port}/case/{case}/v1", api_key="test-key",
                          max_retries=0, timeout=20)
    try:
        chunks = list(llm.stream_chat([ChatMessage(role="user", content="hi")]))
        print(f"{case}: no exception, {len(chunks)} chunks")
        if chunks:
            last = chunks[-1]
            print("  last.message.content:", repr(last.message.content))
            print("  last.message.additional_kwargs:", last.message.additional_kwargs)
            print("  last.raw type:", type(last.raw).__name__, "| raw:", repr(last.raw)[:300])
    except Exception as e:
        print(f"{case}: raised {type(e).__name__}: {e}")
