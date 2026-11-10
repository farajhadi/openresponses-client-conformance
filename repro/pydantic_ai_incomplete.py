"""pydantic-ai Agent.run_stream on a stream that ends in response.incomplete (cut off at max_output_tokens).
Prints the output and the full final ModelResponse, so any finish_reason/status it keeps is visible."""
import asyncio, sys
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

port = sys.argv[1] if len(sys.argv) > 1 else "8765"


async def main():
    for mode in ("run_stream", "run"):
        model = OpenAIResponsesModel("fake-model", provider=OpenAIProvider(
            base_url=f"http://127.0.0.1:{port}/case/response_incomplete/v1", api_key="test-key"))
        agent = Agent(model)
        try:
            if mode == "run_stream":
                async with agent.run_stream("hi") as r:
                    out = await r.get_output()
                    msgs = r.all_messages()
            else:
                r = await agent.run("hi")
                out, msgs = r.output, r.all_messages()
            last = msgs[-1]
            print(f"{mode}: output={out!r}")
            print("  finish_reason:", getattr(last, "finish_reason", "<no attribute>"))
            print("  provider_details:", getattr(last, "provider_details", "<no attribute>"))
        except Exception as e:
            print(f"{mode}: raised {type(e).__name__}: {e}")

asyncio.run(main())
