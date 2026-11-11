"""Turn results/scorecard.json into results/scorecard.md with two scores per library:

  locked rule   exactly the `expect` written in cases/cases.py before any library ran.
  adjusted rule two changes made after the first run, logged in plan/PLAN.md:
    1. Libraries that never expose a response status (marked in clients/adapters_meta.json) are not marked down
       for status on success cases; on response_incomplete they still fail unless the user can see the cut-off text
       AND is told it is incomplete (they cannot, so they fail).
    2. response_failed passes if the library raises OR reports status failed (the case's point is "don't report
       success"; raising is a normal way to say it failed).
    3. response_incomplete passes if the user can tell the answer was cut off: status incomplete, OR an error whose
       message says incomplete / max_output_tokens (same idea as rule 2, applied evenly after Critic's review).
       Whether the partial text still reaches the user is reported in a separate, unscored pair of columns
    (terminal-state vs partial-output), not mixed into the headline score.
Headline = MUST + SSE cases. SHOULD and ROBUST are shown separately.
"""
import json, sys
sys.path.insert(0, "cases")
from cases import CASES

ST = {c["id"]: c["strength"] for c in CASES}
EXP = {c["id"]: c["expect"] for c in CASES}
META = json.load(open("clients/adapters_meta.json"))
d = json.load(open("results/scorecard.json"))


def adjusted(lib, cid, got):
    exp = dict(EXP[cid])
    raised = bool(got.get("raised"))
    if cid == "response_failed":
        return raised or got.get("status") == "failed"
    if cid == "response_incomplete":
        msg = str(got.get("raised") or "").lower()
        return got.get("status") == "incomplete" or ("incomplete" in msg or "max_output_tokens" in msg)
    if not META.get(lib, {}).get("exposes_status", True) and cid != "response_incomplete":
        exp.pop("status", None)
    if META.get(lib, {}).get("status_on_tool_calls", True) is False and "function_call" in exp:
        exp.pop("status", None)  # our adapter interrupts the run in the tool, so there is no status to read
    for k, v in exp.items():
        if k == "error_or_failed":
            if (raised or got.get("status") == "failed") != v:
                return False
        elif got.get(k) != v:
            return False
    return not (raised and "error_or_failed" not in exp)


rows, detail = [], []
for lib, r in d.items():
    head = [c for c in r if ST[c] in ("MUST", "SSE")]
    lk = sum(r[c]["verdict"] == "pass" for c in head)
    ad = sum(adjusted(lib, c, r[c]["got"]) for c in head)
    should = "pass" if adjusted(lib, "unknown_item_type", r["unknown_item_type"]["got"]) else "fail"
    robust = "pass" if adjusted(lib, "truncated_stream", r["truncated_stream"]["got"]) else "fail"
    fails = [c for c in head if not adjusted(lib, c, r[c]["got"])]
    # distinct root causes: failures with the same error text count once
    causes = {str(r[c]["got"].get("raised"))[:40] if r[c]["got"].get("raised") else "wrong result: " + c for c in fails}
    rows.append((ad, lib, lk, should, robust, fails, len(causes)))
rows.sort(reverse=True)
out = ["# Scorecard", "", "Behaviour against our 17 spec-derived cases (11 MUST + 6 SSE). This is not an overall quality ranking, and several "
       "libraries wrap the OpenAI Python SDK, so their results are not independent. The locked score uses the "
       "expectations exactly as written before any library ran; the adjusted score applies the three logged changes "
       "in `report.py`. Failures with the same error count as one root cause.", "",
       "| Library | Locked | Adjusted | Root causes | SHOULD: unknown item | ROBUST: cut-off stream | Failed (adjusted) |",
       "|---|---|---|---|---|---|---|"]
for ad, lib, lk, sh, ro, fails, nc in rows:
    out.append(f"| {lib} | {lk}/17 | {ad}/17 | {nc} | {sh} | {ro} | {', '.join(fails) or '-'} |")
# --- Unscored dimensions for cut-off / failed cases -----------------
# "Knows it failed or was cut off" is the same terminal-state rule already used for the adjusted score
# (and for the ROBUST column on truncated_stream). It is not a new judgement.
# "Keeps the partial text" uses only results/scorecard.json (adapter-recorded final text) and, where
# that text is missing, repro/OUTPUT.txt for streamed events. If streamed events were not measured,
# we say so rather than guessing. Headline scores are unchanged.
EXPECTED_PARTIAL = {
    "response_incomplete": "Hello, wor",
    "truncated_stream": "Hello, ",
}
# (library, case) -> text seen in streamed events, from repro/OUTPUT.txt
REPRO_STREAM_TEXT = {
    ("openai-python", "response_incomplete"): "Hello, wor",
    ("openai-agents", "response_incomplete"): "Hello, wor",
}


def knows_terminal(lib, cid, got):
    if cid == "response_failed":
        return bool(got.get("raised")) or got.get("status") == "failed"
    if cid == "response_incomplete":
        msg = str(got.get("raised") or "").lower()
        return got.get("status") == "incomplete" or ("incomplete" in msg or "max_output_tokens" in msg)
    if cid == "truncated_stream":
        return bool(got.get("raised")) or got.get("status") in ("failed", "incomplete")
    raise ValueError(cid)


def keeps_partial(lib, cid, got):
    if cid == "response_failed":
        return "n/a (no text was sent)"
    expected = EXPECTED_PARTIAL[cid]
    text = got.get("text")
    if text == expected:
        return "yes, in the recorded result"
    if text:
        return f"partial, recorded result is {text!r}"
    stream = REPRO_STREAM_TEXT.get((lib, cid))
    if stream == expected:
        return "yes, from streamed events (not in the final result)"
    if stream:
        return f"partial, streamed events were {stream!r} (not in the final result)"
    return "not in the recorded result; streamed events not measured"


def yn(ok):
    return "yes" if ok else "no"


out += ["",
        "## Cut-off and failed answers: two separate questions",
        "",
        "The headline score only counts whether the app can tell something went wrong (terminal-state).",
        "Whether the library also keeps the text generated before the interruption is reported here, and is",
        "not part of the score. Keeping that partial text is only useful when the library also signals the",
        "cut-off: returning it as if the answer were complete is worse than raising an error.",
        "On the truncated-stream robustness case, langchain-openai, pydantic-ai, llama-index and",
        "openresponses-python return the partial text as if it were complete.",
        "",
        "Sources: the recorded result is `text` in `results/scorecard.json`. For openai-python and",
        "openai-agents on `response_incomplete`, streamed-event text comes from `repro/OUTPUT.txt`.",
        "Where the recorded result has no text and no repro measured the stream, the cell says so.",
        "",
        "### response_incomplete (model stopped early; text sent: \"Hello, wor\")",
        "",
        "| Library | Knows it failed or was cut off | Keeps the partial text |",
        "|---|---|---|"]
for _ad, lib, *_rest in rows:
    got = d[lib]["response_incomplete"]["got"]
    out.append(f"| {lib} | {yn(knows_terminal(lib, 'response_incomplete', got))} | {keeps_partial(lib, 'response_incomplete', got)} |")

out += ["",
        "llama-index's recorded result is the text of the joined stream deltas (see the adapter). The",
        "standalone repro's high-level `last.message.content` was empty; the text is still in the chunks.",
        "",
        "### response_failed (model crashed; no text was sent)",
        "",
        "| Library | Knows it failed or was cut off | Keeps the partial text |",
        "|---|---|---|"]
for _ad, lib, *_rest in rows:
    got = d[lib]["response_failed"]["got"]
    out.append(f"| {lib} | {yn(knows_terminal(lib, 'response_failed', got))} | {keeps_partial(lib, 'response_failed', got)} |")

out += ["",
        "### truncated_stream (robustness, not in the score; text sent: \"Hello, \")",
        "",
        "| Library | Knows it failed or was cut off | Keeps the partial text |",
        "|---|---|---|"]
for _ad, lib, *_rest in rows:
    got = d[lib]["truncated_stream"]["got"]
    out.append(f"| {lib} | {yn(knows_terminal(lib, 'truncated_stream', got))} | {keeps_partial(lib, 'truncated_stream', got)} |")

out += ["", "## What each failure looked like", ""]
for _, lib, _, _, _, fails, _ in rows:
    for c in fails:
        g = json.dumps(d[lib][c]["got"], ensure_ascii=False)
        out.append(f"- **{lib} / {c}**: `{g[:220]}`")
open("results/scorecard.md", "w").write("\n".join(out) + "\n")
print("\n".join(out[:20]))
