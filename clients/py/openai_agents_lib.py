"""openai-agents, Runner.run_streamed with OpenAIResponsesModel on a custom AsyncOpenAI client. The two tools the\ncases call are registered and the run stops at the first tool call; the call is read from the raw model response.\nThe final text for a tool-call run is the tool result, so only function_call is compared there."""
import asyncio
from _common import emit, guard
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.models.openai_responses import OpenAIResponsesModel

set_tracing_disabled(True)


@function_tool
def get_weather(city: str, units: str) -> str:
    return "sunny"


@function_tool
def search(q: str) -> str:
    return "none"


async def run(base):
    client = AsyncOpenAI(base_url=base, api_key="test-key", max_retries=0, timeout=20)
    agent = Agent(name="a", model=OpenAIResponsesModel("fake-model", client), tools=[get_weather, search],
                  tool_use_behavior="stop_on_first_tool")
    r = Runner.run_streamed(agent, "hi", max_turns=1)
    async for _ in r.stream_events():
        pass
    raw = r.raw_responses[-1] if r.raw_responses else None
    fc = None
    if raw:
        fc = next(({"name": o.name, "arguments": o.arguments} for o in raw.output if o.type == "function_call"), None)
    emit(text=None if fc else (r.final_output or None), function_call=fc, status=None)


guard(lambda b: asyncio.run(asyncio.wait_for(run(b), 20)))
