"""openresponses-python parses each `data:` line on its own instead of joining multi-line data as SSE requires."""
import sys
from openresponses.client import OpenResponsesClient

port = sys.argv[1] if len(sys.argv) > 1 else "8765"
client = OpenResponsesClient(base_url=f"http://127.0.0.1:{port}/case/multiline_data", api_key="test-key")
try:
    n = sum(1 for _ in client.create(model="fake-model", input="hi", stream=True))
    print(f"multiline_data: OK, {n} events")
except Exception as e:
    print(f"multiline_data: {type(e).__name__}: {e}")
