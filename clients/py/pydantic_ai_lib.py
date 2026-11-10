"""pydantic-ai, Agent with OpenAIResponsesModel, agent.run_stream(...) as its docs show. Tool calls go to a
registered tool, which records the name and arguments it was called with and then stops the run.
Status comes from the final ModelResponse.finish_reason, pydantic-ai's own normalised field (found by
repro/pydantic_ai_incomplete.py after the first scoring run): stop -> completed, length -> incomplete, error -> failed."""
import asyncio, json
from _common import emit, guard
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

seen = {}
FR = {"stop": "completed", "length": "incomplete", "error": "failed"}


class Stop(Exception):
    pass


async def run(base):
    model = OpenAIResponsesModel("fake-model", provider=OpenAIProvider(base_url=base, api_key="test-key"))
    agent = Agent(model)

    @agent.tool_plain
    def get_weather(city: str, units: str) -> str:
        seen["fc"] = {"name": "get_weather", "arguments": json.dumps({"city": city, "units": units}, ensure_ascii=False)}
        raise Stop

    @agent.tool_plain
    def search(q: str) -> str:
        seen["fc"] = {"name": "search", "arguments": json.dumps({"q": q}, ensure_ascii=False)}
        raise Stop

    try:
        async with agent.run_stream("hi") as result:
            text = await result.get_output()
            fr = getattr(result.all_messages()[-1], "finish_reason", None)
        emit(text=text or None, status=FR.get(fr))
    except Stop:
        emit(function_call=seen["fc"], status=None)


guard(lambda b: asyncio.run(asyncio.wait_for(run(b), 20)))
