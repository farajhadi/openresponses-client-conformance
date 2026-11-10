"""openai-agents Runner.run_streamed on a response.incomplete stream: shows the error message the user gets."""
import asyncio, sys
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled

set_tracing_disabled(True)
port = sys.argv[1] if len(sys.argv) > 1 else "8765"


async def main():
    client = AsyncOpenAI(base_url=f"http://127.0.0.1:{port}/case/response_incomplete/v1", api_key="test-key", max_retries=0)
    agent = Agent(name="a", model=OpenAIResponsesModel(model="fake-model", openai_client=client))
    text = ""
    try:
        r = Runner.run_streamed(agent, "hi")
        async for ev in r.stream_events():
            if ev.type == "raw_response_event" and getattr(ev.data, "type", "") == "response.output_text.delta":
                text += ev.data.delta
        print("OK:", r.final_output)
    except Exception as e:
        print(f"raised {type(e).__name__}: {e}")
        print(f"  text deltas received before the error: {text!r}")

asyncio.run(main())
