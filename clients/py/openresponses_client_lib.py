"""openresponses-client (PyPI, async, aiohttp). Uses client.stream(...) and get_final_response() as its README shows."""
import asyncio
from _common import emit, guard
from openresponses_client import OpenResponsesClient


async def run(base):
    client = OpenResponsesClient(base, api_key="test-key")
    async with client:
        async with client.stream(model="fake-model", input="hi") as stream:
            async for _ in stream:
                pass
            r = await stream.get_final_response()
    fcs = getattr(r, "function_calls", None) or []
    fc = {"name": fcs[0].name, "arguments": fcs[0].arguments} if fcs else None
    emit(text=r.output_text or None, function_call=fc, status=str(getattr(r.status, "value", r.status)))


guard(lambda b: asyncio.run(asyncio.wait_for(run(b), 20)))
