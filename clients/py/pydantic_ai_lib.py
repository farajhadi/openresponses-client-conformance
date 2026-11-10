"""pydantic-ai, Agent with OpenAIResponsesModel, agent.run_stream(...) as its docs show. Tool calls go to a
registered tool, which records the name and arguments it was called with and then stops the run."""
import asyncio, json
from _common import emit, guard
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

seen = {}


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
        emit(text=text or None, status=None)
    except Stop:
        emit(function_call=seen["fc"], status=None)


guard(lambda b: asyncio.run(asyncio.wait_for(run(b), 20)))
