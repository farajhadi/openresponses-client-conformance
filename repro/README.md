# Standalone repros

Each script calls one library directly, with no adapter code, against the fake server in `server/`.
Run all of them with `repro/run_all.sh` (uses each library's venv under `envs/`), which writes `repro/OUTPUT.txt`.

| Script | Shows |
|---|---|
| `openresponses_python_done.py` | Crash on the `data: [DONE]` line the spec allows; the same stream without it works |
| `openresponses_python_multiline.py` | Multi-line `data:` fields are parsed line by line instead of joined |
| `llama_index_failed.py` | `response.failed` / `response.incomplete` end with an empty message and no error |
| `pydantic_ai_incomplete.py` | A cut-off answer is reported through `finish_reason="length"` (our first adapter missed this) |
| `openai_python.py` | Streams the text deltas, then raises on `response.incomplete`; the error doesn't say the answer was cut off, and `get_final_response()` is unavailable. Also raises on a vendor event before `response.created` |
| `openai_agents_incomplete.py` | Raises on `response.incomplete`, with "status=incomplete" in the message |
