"""openresponses-python crashes on the `data: [DONE]` line the spec allows servers to send.
Same case served twice: once ending in [DONE] (baseline), once without it (no_done_sentinel). No adapter code."""
import sys, traceback
from openresponses.client import OpenResponsesClient

port = sys.argv[1] if len(sys.argv) > 1 else "8765"
for case in ("baseline", "no_done_sentinel"):
    client = OpenResponsesClient(base_url=f"http://127.0.0.1:{port}/case/{case}", api_key="test-key")
    try:
        n = sum(1 for _ in client.create(model="fake-model", input="hi", stream=True))
        print(f"{case}: OK, {n} events")
    except Exception as e:
        print(f"{case}: {type(e).__name__}: {e}")
        print("  raised at:", traceback.extract_tb(e.__traceback__)[-2].line)
