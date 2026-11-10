"""Shared bits for Python adapters. An adapter gets the base URL as argv[1] and prints one JSON line:
{"text": str|None, "function_call": {"name","arguments"}|None, "status": str|None, "raised": str|None}
It reports what the library hands its user; the scorer, not the adapter, decides pass or fail."""
import json, sys, traceback


def emit(text=None, function_call=None, status=None, raised=None):
    print(json.dumps({"text": text, "function_call": function_call, "status": status, "raised": raised},
                     ensure_ascii=False), flush=True)


def guard(fn):
    try:
        fn(sys.argv[1])
    except NotImplementedError as e:
        print(json.dumps({"not_supported": str(e)}), flush=True)
    except Exception as e:  # the library raised: record type and message
        emit(raised=f"{type(e).__name__}: {str(e)[:300]}")
        traceback.print_exc(file=sys.stderr)
