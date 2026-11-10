"""openai-python client.responses.stream on: a cut-off response (response.incomplete) and a vendor event sent
before response.created. Collects the events it yields so it's visible whether the partial text arrived first."""
import sys
from openai import OpenAI

port = sys.argv[1] if len(sys.argv) > 1 else "8765"
for case in ("response_incomplete", "unknown_vendor_event_first"):
    client = OpenAI(base_url=f"http://127.0.0.1:{port}/case/{case}/v1", api_key="test-key", max_retries=0)
    seen, text = [], ""
    try:
        with client.responses.stream(model="fake-model", input="hi") as s:
            for ev in s:
                seen.append(ev.type)
                if ev.type == "response.output_text.delta":
                    text += ev.delta
            final = s.get_final_response()
        print(f"{case}: OK status={final.status} text={final.output_text!r}")
    except Exception as e:
        print(f"{case}: raised {type(e).__name__}: {e}")
        print(f"  events seen before the error: {seen}; text deltas so far: {text!r}")
