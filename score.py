"""Run every adapter against every case and write results/scorecard.{json,md}.

Pass rule per case: each key in the case's `expect` must match what the adapter reports.
  error_or_failed=True is met if the library raised OR reported status failed/incomplete-with-error.
Headline = passes over MUST+SSE cases among the cases the library could run."""
import json, os, subprocess, sys, time
sys.path.insert(0, "cases")
from cases import CASES

PORT = 8765
ADAPTERS = json.load(open("clients/adapters.json"))  # {name: [argv...]}


def judge(expect, got):
    for k, v in expect.items():
        if k == "error_or_failed":
            ok = bool(got.get("raised")) or got.get("status") == "failed"
            if ok != v:
                return False
        elif got.get(k) != v:
            return False
    if "error_or_failed" not in expect and got.get("raised"):
        return False
    return True


def main(only=None):
    srv = subprocess.Popen([sys.executable, "server/fake_server.py", "--port", str(PORT), "--log", "logs/server.log"],
                           stdout=subprocess.PIPE)
    srv.stdout.readline()
    res = {}
    try:
        for name, argv in ADAPTERS.items():
            if only and name not in only:
                continue
            res[name] = {}
            for c in CASES:
                base = f"http://127.0.0.1:{PORT}/case/{c['id']}/v1"
                t0 = time.time()
                try:
                    p = subprocess.run(argv + [base], capture_output=True, text=True, timeout=30)
                    line = (p.stdout.strip().splitlines() or ["{}"])[-1]
                    got = json.loads(line) if line.startswith("{") else {"raised": "no output: " + p.stderr[-300:]}
                except subprocess.TimeoutExpired:
                    got = {"raised": "TIMEOUT (hung 30s)"}
                if "not_supported" in got:
                    verdict = "not_supported"
                else:
                    verdict = "pass" if judge(c["expect"], got) else "fail"
                res[name][c["id"]] = {"verdict": verdict, "got": got, "secs": round(time.time() - t0, 2)}
                print(name, c["id"], verdict, flush=True)
    finally:
        srv.terminate()
    os.makedirs("results", exist_ok=True)
    old = json.load(open("results/scorecard.json")) if os.path.exists("results/scorecard.json") else {}
    old.update(res)
    json.dump(old, open("results/scorecard.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
