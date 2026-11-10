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
