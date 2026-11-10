# Plan (locked before running any client library)

**Question.** When an Open Responses server sends a stream with the tricky-but-legal things the spec allows
(no `[DONE]`, vendor events, unknown item types, extra fields, arguments split mid-JSON, odd line endings, failed or
incomplete responses), do the client libraries people actually use hand the right result to their user?

**Cases.** `cases/cases.py`, 19 cases, each quoting the rule it tests (Open Responses spec or the WHATWG SSE standard;
saved copies in `spec/`). Written and committed before any library was installed or run.

**Method.**
1. A fake server (`server/`) replays each case byte for byte at `POST /v1/responses` (stream=true).
2. One small adapter per library calls it the way that library's README shows, and records what the user would get:
   final text, function-call name and arguments, final status, and whether it raised.
3. The scorecard compares that to each case's `expect`. A case passes only on an exact match.

**Scoring (fixed now).** Headline = pass count over MUST + SSE cases (17). SHOULD and ROBUST cases are reported in
separate columns, never in the headline. A library that cannot run a case at all (no streaming support, no function
calls) is marked "not supported", not failed, and the denominator is reported per library.

**Libraries.** About 15 libraries that speak Open Responses or the OpenAI Responses API, chosen from public package
registries; the exact list, versions and install source go in `clients/VERSIONS.md` before scoring. Each runs at its
latest released version on the date of the run.

**Rules.** $0: everything runs locally against the fake server, no model API calls, no AI grader. Bugs found are
written up in the README only; nothing is filed upstream. Any change to cases after the first library run is logged
below with the reason.

## Changes after locking
(none yet)

## Changes after the first scoring run (2026-11-10, logged before writing the README)
1. **Per-case timeout 30 s -> 120 s.** The first run timed out 18 cases. Rerunning them showed most were slow start-up
   (litellm takes about 20-40 s just to import and make one call on this computer), not hangs, so 30 s was unfair. Only cases
   that still give no result after 120 s count as hangs. Only the timed-out cases were rerun.
2. **Two scoring adjustments, reported next to the locked score, never instead of it** (`report.py`):
   - pydantic-ai, openai-agents and llama-index never expose a response status to the user. On success cases the status
     check is skipped for them. On `response_incomplete` they still fail, because the user can't tell the answer was cut off.
   - `response_failed` passes if the library raises or reports `failed`. The case was written to catch "reports success";
     raising is a normal way to report failure, and the locked rule (status must equal `failed`) marked raising as a fail.
Both changes were made after seeing the first run, so the locked scores stay in the scorecard.

## Changes after Critic's review (Nov 10 2026, about 06:30 Paris time)
- **One cut-off rule for everyone (adjusted rule 3).** `response_incomplete` passes if the user can tell the answer was
  cut off: status `incomplete`, or an error whose message says incomplete or max_output_tokens. Before this, raising
  passed on `response_failed` but not on `response_incomplete`, which was uneven. Losing the partial text is now a
  separate, unscored note. The locked scores are unchanged and still shown.
- **Standalone repros in `repro/`.** Each script calls the library directly against the fake server with no adapter
  code (`repro/run_all.sh`, output in `repro/OUTPUT.txt`). They confirmed library behaviour for openresponses-python
  (crashes on `data: [DONE]`; the same case without `[DONE]` works; it separately fails on multi-line `data:`),
  llama-index (`response_failed` returns an empty message with no error; the failure is only in the pass-through
  `chunk.raw` provider object), openai-python (raises on `response.incomplete` after the text was streamed, and on a
  vendor event before `response.created`) and openai-agents (raises with "status=incomplete").
- **Two adapter bugs found by the repros, fixed and rerun.** pydantic-ai *does* expose a status: the final
  `ModelResponse.finish_reason` is `length` on a cut-off answer. The adapter now maps stop/length/error to
  completed/incomplete/failed, and pydantic-ai is no longer marked as having no status. llama-index only carries the
  full message on the `response.completed` chunk, so the adapter now falls back to the joined text deltas when that
  chunk never arrives (this fixes the ", " result on the truncated case). Both libraries were rescored at 120 s
  (`logs/score_rerun_pydantic_llama.log`).
- **Wording.** The scorecard is "behaviour against our 17 spec-derived cases", not a quality ranking; several
  libraries wrap the OpenAI SDK, so their results are not independent. Failures sharing one error count as one root cause.
