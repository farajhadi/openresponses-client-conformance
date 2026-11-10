"""A small reference client written straight from the two specs, used only to check the fake server.

If this client gets every case's `expect`, the server's bytes are well-formed per the SSE standard and the cases are
self-consistent. It is NOT one of the scored libraries.
"""
import json, socket


def sse_events(raw: bytes):
    """WHATWG SSE parsing: decode UTF-8, split lines on CRLF, LF or CR, dispatch on blank line."""
    text = raw.decode("utf-8", errors="replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    data, etype = [], ""
    for line in lines:
        if line == "":
            if data:
                yield etype or "message", "\n".join(data)
            data, etype = [], ""
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "data":
            data.append(value)
        elif field == "event":
            etype = value
    # an event without a trailing blank line is discarded, as the standard says


def fetch(port, case_id):
    s = socket.create_connection(("127.0.0.1", port))
    body = json.dumps({"model": "fake-model", "input": "hi", "stream": True}).encode()
    s.sendall(f"POST /case/{case_id}/v1/responses HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
              f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
    buf = b""
    while chunk := s.recv(65536):
        buf += chunk
    s.close()
    return buf.split(b"\r\n\r\n", 1)[1]


def run(port, case_id):
    """Return what a user of a correct client would see: text, function_call, status, error_or_failed."""
    text, args, name, status, terminal = {}, "", None, None, False
    for _etype, data in sse_events(fetch(port, case_id)):
        if data == "[DONE]":
            break
        e = json.loads(data)
        t = e.get("type", "")
        if t == "response.output_text.delta":
            text[(e["output_index"], e["content_index"])] = text.get((e["output_index"], e["content_index"]), "") + e["delta"]
        elif t == "response.output_item.added" and e["item"].get("type") == "function_call":
            name = e["item"]["name"]
        elif t == "response.function_call_arguments.delta":
            args += e["delta"]
        elif t in ("response.completed", "response.failed", "response.incomplete"):
            status, terminal = e["response"]["status"], True
    out = {"status": status, "error_or_failed": (not terminal) or status == "failed"}
    if text:
        out["text"] = "".join(v for _, v in sorted(text.items()))
    if name:
        out["function_call"] = {"name": name, "arguments": args}
    return out
