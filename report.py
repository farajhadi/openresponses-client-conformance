"""Turn results/scorecard.json into results/scorecard.md with two scores per library:

  locked rule   exactly the `expect` written in cases/cases.py before any library ran.
  adjusted rule two changes made after the first run, logged in plan/PLAN.md:
    1. Libraries that never expose a response status (marked in clients/adapters_meta.json) are not marked down
       for status on success cases; on response_incomplete they still fail unless the user can see the cut-off text
       AND is told it is incomplete (they cannot, so they fail).
    2. response_failed passes if the library raises OR reports status failed (the case's point is "don't report
       success"; raising is a normal way to say it failed).
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
    if not META.get(lib, {}).get("exposes_status", True) and cid != "response_incomplete":
        exp.pop("status", None)
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
    rows.append((ad, lib, lk, should, robust, fails))
rows.sort(reverse=True)
out = ["# Scorecard", "", "Out of 17 required cases (11 MUST + 6 SSE). The locked score uses the expectations exactly as written "
       "before any library ran; the adjusted score applies the two logged changes in `report.py`.", "",
       "| Library | Adjusted | Locked | SHOULD: unknown item | ROBUST: cut-off stream | Failed (adjusted) |", "|---|---|---|---|---|---|"]
for ad, lib, lk, sh, ro, fails in rows:
    out.append(f"| {lib} | {ad}/17 | {lk}/17 | {sh} | {ro} | {', '.join(fails) or '-'} |")
out += ["", "## What each failure looked like", ""]
for _, lib, _, _, _, fails in rows:
    for c in fails:
        g = json.dumps(d[lib][c]["got"], ensure_ascii=False)
        out.append(f"- **{lib} / {c}**: `{g[:220]}`")
open("results/scorecard.md", "w").write("\n".join(out) + "\n")
print("\n".join(out[:20]))
