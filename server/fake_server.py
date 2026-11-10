"""Fake Open Responses server that replays the cases in cases/cases.py.

Each case lives under its own base URL, so a client library only needs its base_url pointed at it:
    http://127.0.0.1:<port>/case/<case_id>/v1     ->  POST .../responses  (any body; the reply is always the case)
Run:  python server/fake_server.py --port 8765
Standard library only, so it adds nothing to install.
"""
import argparse, json, os, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cases"))
from cases import CASES  # noqa: E402

BY_ID = {c["id"]: c for c in CASES}


def render(case):
    """Turn a case into the exact bytes the server sends, as a list of per-event byte strings."""
    t = case["transport"]
    nl = t.get("newline", "\n")
    out = []
    for e in case["events"]:
        payload = json.dumps(e, ensure_ascii=False)
        if t.get("split_data"):
            # split after the first comma: SSE joins data lines with "\n", which is valid JSON whitespace there
            i = payload.index(",") + 1
            data = f"data: {payload[:i]}{nl}data: {payload[i:]}{nl}"
        else:
            data = f"data: {payload}{nl}"
        block = f"event: {e['type']}{nl}{data}{nl}"
        if t.get("comments"):
            block = f": keep-alive{nl}{block}"
        out.append(block.encode("utf-8"))
    if "cut_after" in t:
        out = out[: t["cut_after"]]
    elif t.get("done"):
        out.append(f"data: [DONE]{nl}{nl}".encode())
    return out


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    log_path = None

    def log_message(self, fmt, *args):  # keep stdout clean; requests go to the log file
        if self.log_path:
            with open(self.log_path, "a") as f:
                f.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def do_POST(self):
        parts = self.path.strip("/").split("/")
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        if len(parts) != 4 or parts[0] != "case" or parts[2] != "v1" or parts[3] != "responses" or parts[1] not in BY_ID:
            msg = json.dumps({"error": {"message": f"unknown path {self.path}", "type": "not_found"}}).encode()
            self.send_response(404); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg))); self.end_headers(); self.wfile.write(msg)
            return
        case = BY_ID[parts[1]]
        try:
            req = json.loads(body or b"{}")
        except ValueError:
            req = {}
        if Handler.log_path:
            with open(Handler.log_path, "a") as f:
                f.write(json.dumps({"case": case["id"], "stream": req.get("stream")}) + "\n")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")  # no Content-Length: the body ends when the connection closes
        self.end_headers()
        size = case["transport"].get("chunk")
        for block in render(case):
            pieces = [block[i:i + size] for i in range(0, len(block), size)] if size else [block]
            for p in pieces:
                self.wfile.write(p); self.wfile.flush()
        self.close_connection = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--log", default=None)
    a = ap.parse_args()
    Handler.log_path = a.log
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"serving {len(CASES)} cases on http://127.0.0.1:{a.port}/case/<id>/v1", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
