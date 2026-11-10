"""Test cases for Open Responses *clients*, written from the spec before any client library was run.

Sources (saved copies in spec/, fetched 2026-11-10):
  * Open Responses specification, https://www.openresponses.org/specification  (quoted as "OR")
  * WHATWG HTML Living Standard, server-sent events section, https://html.spec.whatwg.org/multipage/server-sent-events.html
    (quoted as "SSE"; Open Responses streams are SSE, so a client must parse SSE correctly)

Each case is one fake-server reply to POST /v1/responses with stream=true, described as a list of SSE events plus
transport options, and the outcome a correct client must show. The scorecard compares what each client hands to
its user (final text, function-call name and arguments, final status, whether it raised) with `expect`.

Strength of each case, fixed here before running anything:
  MUST    the spec puts an explicit requirement on clients, or a client that fails loses data the spec guarantees
  SHOULD  the spec recommends the behaviour ("clients SHOULD ...")
  SSE     required by the SSE standard the transport uses
  ROBUST  not stated as a client rule; a sensible expectation derived from a server MUST (reported separately)
The headline score counts MUST and SSE cases only.
"""

RID, MID, FID = "resp_test_1", "msg_test_1", "fc_test_1"


def resp(status, output=None, **extra):
    r = {"id": RID, "object": "response", "status": status, "model": "fake-model", "output": output or [],
         "created_at": 1762750000, "error": None, "incomplete_details": None}
    r.update(extra)
    return r


def msg_item(text, status="completed", parts=None):
    parts = parts if parts is not None else [text]
    return {"id": MID, "type": "message", "role": "assistant", "status": status,
            "content": [{"type": "output_text", "text": p, "annotations": []} for p in parts]}


def fc_item(name, args, status="completed"):
    return {"id": FID, "type": "function_call", "call_id": "call_1", "name": name, "arguments": args, "status": status}


def text_events(chunks, item=None, output_index=0, logprobs=True, final_status="completed", parts=None):
    """Standard event sequence for one assistant message streamed as text deltas (content part index 0)."""
    text = "".join(chunks)
    ev = [{"type": "response.created", "response": resp("in_progress")},
          {"type": "response.in_progress", "response": resp("in_progress")},
          {"type": "response.output_item.added", "output_index": output_index,
           "item": {**msg_item("", "in_progress"), "content": []}},
          {"type": "response.content_part.added", "item_id": MID, "output_index": output_index, "content_index": 0,
           "part": {"type": "output_text", "text": "", "annotations": []}}]
    for c in chunks:
        d = {"type": "response.output_text.delta", "item_id": MID, "output_index": output_index,
             "content_index": 0, "delta": c}
        if logprobs:
            d["logprobs"] = []
        ev.append(d)
    item = item or msg_item(text)
    ev += [{"type": "response.output_text.done", "item_id": MID, "output_index": output_index, "content_index": 0,
            "text": text},
           {"type": "response.content_part.done", "item_id": MID, "output_index": output_index, "content_index": 0,
            "part": {"type": "output_text", "text": text, "annotations": []}},
           {"type": "response.output_item.done", "output_index": output_index, "item": item},
           {"type": "response.completed", "response": resp(final_status, [item])}]
    return ev


HELLO = ["Hello", ", ", "world", "!"]
ARABIC = ["مرحبا", " بالعالم ", "😀"]   # multi-byte UTF-8 (2-byte Arabic, 4-byte emoji)


def fc_events(name, arg_chunks):
    args = "".join(arg_chunks)
    added = fc_item(name, "", "in_progress")
    done = fc_item(name, args)
    ev = [{"type": "response.created", "response": resp("in_progress")},
          {"type": "response.output_item.added", "output_index": 0, "item": added}]
    ev += [{"type": "response.function_call_arguments.delta", "item_id": FID, "output_index": 0, "delta": c}
           for c in arg_chunks]
    ev += [{"type": "response.function_call_arguments.done", "item_id": FID, "output_index": 0, "arguments": args},
           {"type": "response.output_item.done", "output_index": 0, "item": done},
           {"type": "response.completed", "response": resp("completed", [done])}]
    return ev


def insert(ev, at, new):
    return ev[:at] + new + ev[at:]


# transport options understood by the fake server:
#   done: send "data: [DONE]" after the terminal event     chunk: split the byte stream into pieces of this size
#   newline: "\n" | "\r\n" | "\r"                          comments: send ": keep-alive" lines between events
#   split_data: put each JSON payload on two data: lines    cut_after: close the connection after N events
CASES = [
    dict(id="baseline", strength="MUST", events=text_events(HELLO), transport={"done": True},
         expect={"text": "Hello, world!", "status": "completed"},
         why="Control: a plain text stream with [DONE]. A client failing this is not exercised by the other cases."),
    dict(id="no_done_sentinel", strength="MUST", events=text_events(HELLO), transport={"done": False},
         expect={"text": "Hello, world!", "status": "completed"},
         why='OR: "Servers MAY send the literal string [DONE] after that event. Clients MUST also accept the stream '
             'ending after the terminal response event without [DONE]."'),
    dict(id="unknown_vendor_event", strength="MUST",
         events=insert(text_events(HELLO), 5, [{"type": "acme:trace_event", "span": "decode", "ms": 12}]),
         transport={"done": True}, expect={"text": "Hello, world!", "status": "completed"},
         why='OR: "Clients that do not understand a given extended event type MUST be able to ignore it safely '
             'without losing the ability to reconstruct the canonical response."'),
    dict(id="unknown_vendor_event_first", strength="MUST",
         events=[{"type": "acme:trace_event", "phase": "start"}] + text_events(HELLO),
         transport={"done": True}, expect={"text": "Hello, world!", "status": "completed"},
         why="Same rule as unknown_vendor_event, with the unknown event arriving before response.created."),
    dict(id="unknown_item_type", strength="SHOULD",
         events=insert(text_events(HELLO, output_index=1), 2, [
             {"type": "response.output_item.added", "output_index": 0,
              "item": {"id": "x_1", "type": "acme:search_result", "status": "in_progress"}},
             {"type": "response.output_item.done", "output_index": 0,
              "item": {"id": "x_1", "type": "acme:search_result", "status": "completed", "hits": 3}}]),
         transport={"done": True}, expect={"text": "Hello, world!", "status": "completed"},
         why='OR: "clients SHOULD be prepared to encounter unknown item types (for example, by ignoring them '
             'gracefully or treating them as opaque records)."'),
    dict(id="extra_fields", strength="MUST",
         events=[{**e, "acme_latency_ms": 5} for e in text_events(HELLO)], transport={"done": True},
         expect={"text": "Hello, world!", "status": "completed"},
         why='OR: "implementors MAY extend existing schemas with additional, implementation-specific fields" and '
             '"extensions MUST NOT alter required core behavior". A client that rejects unknown fields loses the response.'),
    dict(id="logprobs_absent", strength="MUST", events=text_events(HELLO, logprobs=False), transport={"done": True},
         expect={"text": "Hello, world!", "status": "completed"},
         why="OR changelog 2026-04-24: \"Made logprobs optional in output-text objects and streaming events.\""),
    dict(id="function_call_split_args", strength="MUST",
         events=fc_events("get_weather", ['{"ci', 'ty": "Pa', 'ris", "u', 'nits": "c"', '}']),
         transport={"done": True},
         expect={"function_call": {"name": "get_weather", "arguments": '{"city": "Paris", "units": "c"}'},
                 "status": "completed"},
         why="OR: function_call_arguments.delta appends to the arguments; deltas may split JSON anywhere."),
    dict(id="function_call_unicode_args", strength="MUST",
         events=fc_events("search", ['{"q": "مر', 'حبا 😀"}']), transport={"done": True, "chunk": 3},
         expect={"function_call": {"name": "search", "arguments": '{"q": "مرحبا 😀"}'}, "status": "completed"},
         why="Arguments with multi-byte characters, delivered 3 bytes at a time."),
    dict(id="byte_by_byte", strength="SSE", events=text_events(HELLO), transport={"done": True, "chunk": 1},
         expect={"text": "Hello, world!", "status": "completed"},
         why="SSE: the stream is a byte stream; event boundaries are blank lines, not network packets."),
    dict(id="utf8_split_across_chunks", strength="SSE", events=text_events(ARABIC),
         transport={"done": True, "chunk": 5},
         expect={"text": "".join(ARABIC), "status": "completed"},
         why="SSE: the stream is decoded as UTF-8; a multi-byte character can be split across network reads."),
    dict(id="crlf_newlines", strength="SSE", events=text_events(HELLO), transport={"done": True, "newline": "\r\n"},
         expect={"text": "Hello, world!", "status": "completed"},
         why='SSE: lines end with "a U+000D CARRIAGE RETURN U+000A LINE FEED (CRLF) character pair, a single U+000A '
             'LINE FEED (LF) character ..., or a single U+000D CARRIAGE RETURN (CR) character".'),
    dict(id="cr_newlines", strength="SSE", events=text_events(HELLO), transport={"done": True, "newline": "\r"},
         expect={"text": "Hello, world!", "status": "completed"},
         why="SSE: same rule, bare CR line endings."),
    dict(id="comment_lines", strength="SSE", events=text_events(HELLO), transport={"done": True, "comments": True},
         expect={"text": "Hello, world!", "status": "completed"},
         why='SSE: "If the line starts with a U+003A COLON character (:) Ignore the line." (used as keep-alives).'),
    dict(id="multiline_data", strength="SSE", events=text_events(HELLO), transport={"done": True, "split_data": True},
         expect={"text": "Hello, world!", "status": "completed"},
         why="SSE: several data: lines in one event are joined with a newline; the joined JSON is still valid."),
    dict(id="multiple_content_parts", strength="MUST",
         events=None, transport={"done": True},  # built below
         expect={"text": "Hello, world!", "status": "completed"},
         why='OR: "Items with content MAY emit multiple content parts, following the pattern above."'),
    dict(id="response_failed", strength="MUST",
         events=[{"type": "response.created", "response": resp("in_progress")},
                 {"type": "response.failed", "response": resp("failed", error={"code": "server_error",
                                                                               "message": "model crashed"})}],
         transport={"done": False}, expect={"status": "failed", "error_or_failed": True},
         why="OR: response.failed is a terminal event; the client must not report success with empty text."),
    dict(id="response_incomplete", strength="MUST",
         events=text_events(["Hello", ", wor"], item=msg_item("Hello, wor", status="incomplete"),
                            final_status="incomplete")[:-1]
         + [{"type": "response.incomplete",
             "response": resp("incomplete", [msg_item("Hello, wor", status="incomplete")],
                              incomplete_details={"reason": "max_output_tokens"})}],
         transport={"done": False}, expect={"text": "Hello, wor", "status": "incomplete"},
         why='OR: "If an item ends in a terminal state ... the containing response also MUST be in an incomplete '
             'state." The client must expose incomplete, not completed.'),
    dict(id="truncated_stream", strength="ROBUST", events=text_events(HELLO), transport={"cut_after": 6},
         expect={"error_or_failed": True},
         why='OR: "The stream MUST include a terminal response event". A stream that ends without one was cut off; '
             "a client that reports success hides lost output. Not stated as a client rule, so reported separately."),
]

# multiple content parts: two output_text parts in one message
_mp = [{"type": "response.created", "response": resp("in_progress")},
       {"type": "response.output_item.added", "output_index": 0, "item": {**msg_item("", "in_progress"), "content": []}}]
for ci, part in enumerate(["Hello, ", "world!"]):
    _mp += [{"type": "response.content_part.added", "item_id": MID, "output_index": 0, "content_index": ci,
             "part": {"type": "output_text", "text": "", "annotations": []}},
            {"type": "response.output_text.delta", "item_id": MID, "output_index": 0, "content_index": ci,
             "delta": part, "logprobs": []},
            {"type": "response.output_text.done", "item_id": MID, "output_index": 0, "content_index": ci,
             "text": part},
            {"type": "response.content_part.done", "item_id": MID, "output_index": 0, "content_index": ci,
             "part": {"type": "output_text", "text": part, "annotations": []}}]
_full = msg_item("Hello, world!", parts=["Hello, ", "world!"])
_mp += [{"type": "response.output_item.done", "output_index": 0, "item": _full},
        {"type": "response.completed", "response": resp("completed", [_full])}]
next(c for c in CASES if c["id"] == "multiple_content_parts")["events"] = _mp

# sequence numbers: monotonically increasing from 0, as OR requires of servers
for c in CASES:
    n = 0
    for e in c["events"]:
        e["sequence_number"] = n
        n += 1

if __name__ == "__main__":
    import collections
    print(len(CASES), "cases", dict(collections.Counter(c["strength"] for c in CASES)))
