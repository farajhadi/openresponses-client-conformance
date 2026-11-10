"""Check the fake server against the reference client: every case's expectation must hold. Run: python tests/test_server.py"""
import os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cases"))
from cases import CASES  # noqa: E402
from reference_client import run  # noqa: E402

PORT = 8799
root = os.path.join(os.path.dirname(__file__), "..")
srv = subprocess.Popen([sys.executable, os.path.join(root, "server", "fake_server.py"), "--port", str(PORT)],
                       stdout=subprocess.PIPE)
srv.stdout.readline()
fails = 0
try:
    for c in CASES:
        got = run(PORT, c["id"])
        bad = {k: (v, got.get(k)) for k, v in c["expect"].items() if got.get(k) != v}
        print(("ok  " if not bad else "FAIL"), c["id"], bad or "")
        fails += bool(bad)
finally:
    srv.terminate()
print(f"{len(CASES) - fails}/{len(CASES)} cases replay correctly")
sys.exit(1 if fails else 0)
