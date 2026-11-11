# Scorecard

Behaviour against our 17 spec-derived cases (11 MUST + 6 SSE). This is not an overall quality ranking, and several libraries wrap the OpenAI Python SDK, so their results are not independent. The locked score uses the expectations exactly as written before any library ran; the adjusted score applies the three logged changes in `report.py`. Failures with the same error count as one root cause.

| Library | Locked | Adjusted | Root causes | SHOULD: unknown item | ROBUST: cut-off stream | Failed (adjusted) |
|---|---|---|---|---|---|---|
| pydantic-ai | 14/17 | 17/17 | 0 | pass | fail | - |
| openresponses-client | 17/17 | 17/17 | 0 | pass | pass | - |
| openai-agents | 0/17 | 17/17 | 0 | pass | pass | - |
| litellm | 16/17 | 17/17 | 0 | pass | pass | - |
| langchain-openai | 16/17 | 17/17 | 0 | pass | fail | - |
| any-llm | 17/17 | 17/17 | 0 | pass | fail | - |
| openai-python | 14/17 | 15/17 | 2 | pass | pass | unknown_vendor_event_first, response_incomplete |
| llama-index | 0/17 | 15/17 | 2 | pass | fail | response_failed, response_incomplete |
| openresponses-python | 3/17 | 3/17 | 2 | fail | fail | baseline, unknown_vendor_event, unknown_vendor_event_first, extra_fields, logprobs_absent, function_call_split_args, function_call_unicode_args, byte_by_byte, utf8_split_across_chunks, crlf_newlines, cr_newlines, comment_lines, multiline_data, multiple_content_parts |

## Cut-off and failed answers: two separate questions

The headline score only counts whether the app can tell something went wrong (terminal-state).
Whether the library also keeps the text generated before the interruption is reported here, and is
not part of the score. Keeping that partial text is only useful when the library also signals the
cut-off: returning it as if the answer were complete is worse than raising an error.
On the truncated-stream robustness case, langchain-openai, pydantic-ai, llama-index and
openresponses-python return the partial text as if it were complete.

Sources: the recorded result is `text` in `results/scorecard.json`. For openai-python and
openai-agents on `response_incomplete`, streamed-event text comes from `repro/OUTPUT.txt`.
Where the recorded result has no text and no repro measured the stream, the cell says so.

### response_incomplete (model stopped early; text sent: "Hello, wor")

| Library | Knows it failed or was cut off | Keeps the partial text |
|---|---|---|
| pydantic-ai | yes | yes, in the recorded result |
| openresponses-client | yes | yes, in the recorded result |
| openai-agents | yes | yes, from streamed events (not in the final result) |
| litellm | yes | yes, in the recorded result |
| langchain-openai | yes | yes, in the recorded result |
| any-llm | yes | yes, in the recorded result |
| openai-python | no | yes, from streamed events (not in the final result) |
| llama-index | no | yes, in the recorded result |
| openresponses-python | yes | yes, in the recorded result |

llama-index's recorded result is the text of the joined stream deltas (see the adapter). The
standalone repro's high-level `last.message.content` was empty; the text is still in the chunks.

### response_failed (model crashed; no text was sent)

| Library | Knows it failed or was cut off | Keeps the partial text |
|---|---|---|
| pydantic-ai | yes | n/a (no text was sent) |
| openresponses-client | yes | n/a (no text was sent) |
| openai-agents | yes | n/a (no text was sent) |
| litellm | yes | n/a (no text was sent) |
| langchain-openai | yes | n/a (no text was sent) |
| any-llm | yes | n/a (no text was sent) |
| openai-python | yes | n/a (no text was sent) |
| llama-index | no | n/a (no text was sent) |
| openresponses-python | yes | n/a (no text was sent) |

### truncated_stream (robustness, not in the score; text sent: "Hello, ")

| Library | Knows it failed or was cut off | Keeps the partial text |
|---|---|---|
| pydantic-ai | no | yes, in the recorded result |
| openresponses-client | yes | not in the recorded result; streamed events not measured |
| openai-agents | yes | not in the recorded result; streamed events not measured |
| litellm | yes | not in the recorded result; streamed events not measured |
| langchain-openai | no | yes, in the recorded result |
| any-llm | no | not in the recorded result; streamed events not measured |
| openai-python | yes | not in the recorded result; streamed events not measured |
| llama-index | no | yes, in the recorded result |
| openresponses-python | no | yes, in the recorded result |

## What each failure looked like

- **openai-python / unknown_vendor_event_first**: `{"text": null, "function_call": null, "status": null, "raised": "RuntimeError: Expected to have received `response.created` before `acme:trace_event`"}`
- **openai-python / response_incomplete**: `{"text": null, "function_call": null, "status": null, "raised": "RuntimeError: Didn't receive a `response.completed` event."}`
- **llama-index / response_failed**: `{"text": null, "function_call": null, "status": null, "raised": null}`
- **llama-index / response_incomplete**: `{"text": "Hello, wor", "function_call": null, "status": null, "raised": null}`
- **openresponses-python / baseline**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / unknown_vendor_event**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / unknown_vendor_event_first**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / extra_fields**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / logprobs_absent**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / function_call_split_args**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / function_call_unicode_args**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / byte_by_byte**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / utf8_split_across_chunks**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / crlf_newlines**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / cr_newlines**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / comment_lines**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
- **openresponses-python / multiline_data**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 29 (char 28)"}`
- **openresponses-python / multiple_content_parts**: `{"text": null, "function_call": null, "status": null, "raised": "JSONDecodeError: Expecting value: line 1 column 2 (char 1)"}`
