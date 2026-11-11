# Do LLM client libraries handle streamed responses correctly?

When a chat model "types" its answer to you, the server sends the answer as a stream of small events. The
[Open Responses specification](https://www.openresponses.org/specification) says what those events can look like,
and it allows a few awkward-but-legal things: an optional `[DONE]` line at the end, extra event types from a vendor,
extra fields, a function call's arguments split mid-way, different line endings, and answers that fail or get cut off.

This project checks how **9 popular Python libraries** behave when a server sends exactly those things. A fake server
replays 19 hand-written cases byte for byte (17 count toward the score), and a small script per library uses it the way the library's own docs
show. The fake server needs no API key and makes no model calls, so everything is free and runs offline.

**Read this as "behaviour against our 17 spec-derived cases", not a quality ranking.** The cases cover the corners of
the spec, not everyday use. Several libraries are built on top of the OpenAI Python SDK, so their results are not
independent of each other.

## What we found

| Library | Version | Score (locked) | Score (adjusted) | Distinct problems |
|---|---|---|---|---|
| openresponses-client | 0.0.2 | 17/17 | 17/17 | 0 |
| litellm | 1.108.4 | 16/17 | 17/17 | 0 |
| langchain-openai | 1.7.4 | 16/17 | 17/17 | 0 |
| any-llm-sdk | 1.48.0 | 17/17 | 17/17 | 0 |
| pydantic-ai-slim | 2.66.0 | 14/17 | 17/17 | 0 |
| openai-agents | 0.24.0 | 0/17 | 17/17 | 0 |
| openai (Python SDK) | 3.48.0 | 14/17 | 15/17 | 2 |
| llama-index-llms-openai | 0.8.3 | 0/17 | 15/17 | 2 |
| openresponses-python | 0.1.4 | 3/17 | 3/17 | 2 |

The large locked-to-adjusted swings for openai-agents (0/17 to 17/17) and llama-index (0/17 to 15/17) are mainly because those two libraries never expose a response status, so the locked rule fails every case that expected one. The adjusted rule skips the status check on success cases, and counts raising an error as correctly reporting a failed or cut-off answer.

The **locked** score uses the expected results exactly as written before any library ran. The **adjusted** score
applies three rule changes made afterwards, each logged with its reason in [`plan/PLAN.md`](plan/PLAN.md) (summary
under "How it was scored"). Both are shown so nobody has to trust the changes. Full per-case results are in
[`results/scorecard.md`](results/scorecard.md).

Each problem below was reproduced by a short script in [`repro/`](repro/) that calls the library directly, with none
of our adapter code (output in [`repro/OUTPUT.txt`](repro/OUTPUT.txt)).

- **openresponses-python crashes on the `[DONE]` line.** The spec says servers *may* end a stream with `data: [DONE]`.
  This library tries to read that line as JSON and crashes, so it fails every case that ends that way (13 of the 17).
  This is one bug, not 13: the same stream without `[DONE]` works. Separately, it reads each `data:` line on its own
  instead of joining multi-line data as the streaming standard requires (1 case).
- **The OpenAI Python SDK's stream helper gives no final result for a cut-off answer, and its error doesn't say why.**
  When the model stops early (for example at a length limit), the server sends `response.incomplete`. The helper
  (`client.responses.stream`) does stream the text deltas — the app receives "Hello, wor" — then raises a
  `RuntimeError` ("Didn't receive a `response.completed` event") that doesn't say the answer was cut off. After the
  exception, `get_final_response()` is unavailable, so the final assembled response is lost. It also crashes if a
  vendor's custom event arrives before the first standard event, which the spec says clients must ignore safely.
- **llama-index reports a failed answer as an empty success.** On `response.failed` it raises nothing and returns an
  empty message. The failure is visible only if you dig into the raw provider object attached to each chunk. On a
  cut-off answer it likewise gives no sign that the answer is incomplete.

Two separate questions for cut-off and failed answers (only the first is in the score). Keeping the partial text
is only useful when the library also signals the cut-off. Full tables are in
[`results/scorecard.md`](results/scorecard.md).

**Cut-off answer** (the model stopped early; text sent: "Hello, wor"):

| Library | Knows it failed or was cut off | Keeps the partial text |
|---|---|---|
| openresponses-client | yes | yes, in the recorded result |
| litellm | yes | yes, in the recorded result |
| langchain-openai | yes | yes, in the recorded result |
| any-llm-sdk | yes | yes, in the recorded result |
| pydantic-ai-slim | yes | yes, in the recorded result |
| openai-agents | yes | yes, from streamed events (not in the final result) |
| openai (Python SDK) | no | yes, from streamed events (not in the final result) |
| llama-index-llms-openai | no | yes, in the recorded result |
| openresponses-python | yes | yes, in the recorded result |

For openai-agents and the OpenAI SDK, the standalone repros show the app does receive the streamed text ("Hello, wor"),
but it is not in the final assembled result. For llama-index, the recorded result is the joined stream deltas; the
repro's high-level `last.message.content` was empty.

**Failed answer** (the model crashed; no text was sent): every library except llama-index tells the app it failed.
llama-index returns an empty success.

**Stream that just stops** (a separate "robustness" case, not in the score; text sent: "Hello, ").
openresponses-client, litellm, openai-agents and the OpenAI SDK raise an error (whether they also kept the streamed
text was not measured). langchain-openai, pydantic-ai, llama-index and openresponses-python hand back the partial
text as if it were the whole answer. any-llm returns nothing with no error.

Everything else passed: vendor events mid-stream, extra fields, missing `logprobs`, function-call arguments split
anywhere (including mid-way through an emoji), one byte at a time, `\r\n` and `\r` line endings, keep-alive comments
and several content parts.

Why it matters: this addresses a gap Simon Willison (developer and AI blogger) described on
[15 Jan 2026](https://simonwillison.net/2026/Jan/15/open-responses/), when Open Responses launched: the spec has
conformance tests for servers only, and "What's missing is the equivalent for clients." Our tests are a small,
Python-only start on that.

## How it was scored

- **Cases** ([`cases/cases.py`](cases/cases.py)): 19 cases, each quoting the rule it tests from the Open Responses
  spec or the [WHATWG server-sent events standard](https://html.spec.whatwg.org/multipage/server-sent-events.html)
  (saved copies in `spec/`). They were committed before any library was installed. The headline counts the 11 "MUST"
  and 6 streaming-format cases (17). One "SHOULD" case and one robustness case are reported separately.
- **Adapters** (`clients/py/`): one short script per library, written the way its docs show. Each records what the
  user ends up with: the text, the function call, the status, and whether it raised an error.
- **Changes after the first run** (adjusted score only):
  1. Some libraries never expose a response status, so they aren't marked down for a missing status on cases that
     succeed.
  2. On a failed response, raising an error counts as correctly reporting the failure.
  3. On a cut-off response, it passes if the user can tell it was cut off: either the status says incomplete, or the
     error message does. Whether the partial text still reaches the user is a separate, unscored column in the
     scorecard, next to whether the app can tell it failed.
- **Our own mistakes, found and fixed.** The repro scripts showed two adapter bugs, both of them ours: pydantic-ai
  *does* report a cut-off answer (as `finish_reason="length"`), and llama-index only puts the full text on the final
  "completed" chunk. Both adapters were fixed and those libraries rescored. Earlier, a 30-second time limit turned out
  to be measuring library start-up time, so every library was rescored with 120 seconds.

## Caveats

- 19 cases are a sample of the spec's corners, not proof that a library is correct.
- Each library was tested at one version on 10 Nov 2026 (`clients/VERSIONS.md`). Bugs may already be fixed in
  newer versions.
- Each adapter is our reading of the library's docs. A different, equally reasonable usage could score differently;
  the repro scripts are there so each failure can be checked without our adapters.
- Python only. JavaScript libraries are installed under `clients/js` but haven't been tested yet.
- No bugs have been reported upstream. They are written up here only.

## Reproduce

```bash
# one isolated environment per library (Python 3.12; openresponses-client needs 3.14), versions in clients/VERSIONS.md
uv venv envs/openai --python 3.12 && uv pip install --python envs/openai/bin/python openai==3.48.0   # etc.
python3 tests/test_server.py             # checks the fake server against a reference client
python3 score.py                         # runs every adapter against every case -> results/scorecard.json
python3 report.py                        # -> results/scorecard.md
repro/run_all.sh                         # standalone repros -> repro/OUTPUT.txt
```
