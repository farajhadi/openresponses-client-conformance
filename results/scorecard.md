# Scorecard

Out of 17 required cases (11 MUST + 6 SSE). The locked score uses the expectations exactly as written before any library ran; the adjusted score applies the two logged changes in `report.py`.

| Library | Adjusted | Locked | SHOULD: unknown item | ROBUST: cut-off stream | Failed (adjusted) |
|---|---|---|---|---|---|
| openresponses-client | 17/17 | 17/17 | pass | pass | - |
| litellm | 17/17 | 16/17 | pass | pass | - |
| langchain-openai | 17/17 | 16/17 | pass | fail | - |
| any-llm | 17/17 | 17/17 | pass | fail | - |
| pydantic-ai | 16/17 | 0/17 | pass | fail | response_incomplete |
| openai-agents | 16/17 | 0/17 | pass | pass | response_incomplete |
| openai-python | 15/17 | 14/17 | pass | pass | unknown_vendor_event_first, response_incomplete |
| llama-index | 15/17 | 0/17 | pass | fail | response_failed, response_incomplete |
| openresponses-python | 3/17 | 3/17 | fail | fail | baseline, unknown_vendor_event, unknown_vendor_event_first, extra_fields, logprobs_absent, function_call_split_args, function_call_unicode_args, byte_by_byte, utf8_split_across_chunks, crlf_newlines, cr_newlines, comment_lines, multiline_data, multiple_content_parts |

## What each failure looked like

- **pydantic-ai / response_incomplete**: `{"text": "Hello, wor", "function_call": null, "status": null, "raised": null}`
- **openai-agents / response_incomplete**: `{"text": null, "function_call": null, "status": null, "raised": "ModelBehaviorError: Responses stream ended with terminal event `response.incomplete`. status=incomplete; incomplete_details=IncompleteDetails(reason='max_o`
- **openai-python / unknown_vendor_event_first**: `{"text": null, "function_call": null, "status": null, "raised": "RuntimeError: Expected to have received `response.created` before `acme:trace_event`"}`
- **openai-python / response_incomplete**: `{"text": null, "function_call": null, "status": null, "raised": "RuntimeError: Didn't receive a `response.completed` event."}`
- **llama-index / response_failed**: `{"text": null, "function_call": null, "status": null, "raised": null}`
- **llama-index / response_incomplete**: `{"text": null, "function_call": null, "status": null, "raised": null}`
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
