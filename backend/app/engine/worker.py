import sys
from .tracer import Tracer
from .sandbox import get_sandbox_globals


def worker_main(code, conn, mode):

    tracer = Tracer(mode=mode)
    sandbox_globals = get_sandbox_globals()

    error = None

    try:
        # 🔴 DETAILED MODE → full tracing
        if mode == "detailed":
            sys.settrace(tracer.trace)
            exec(code, sandbox_globals, sandbox_globals)
            sys.settrace(None)

        # ⚡ FAST MODE → NO tracing (critical fix)
        else:
            exec(code, sandbox_globals, sandbox_globals)

            from .serializer import safe_serialize

            # manually create ONE final snapshot (SAFE)
            final_locals = {}

            for k, v in sandbox_globals.items():
                if k.startswith("__"):
                    continue
                final_locals[k] = safe_serialize(v)

            tracer.snapshots.append({
                "step": 1,
                "event": "line",
                "line_no": 0,
                "function": "global",
                "stack": ["global"],
                "locals": final_locals,
                "delta": None,
                "is_full": True
            })

            # build variable history (basic)
            for k, v in final_locals.items():
                tracer.variable_history[k] = [(0, v)]

            # simple line index
            tracer.line_index = {0: [1]}

    except Exception as e:
        error = type(e).__name__ + ": " + str(e)

    finally:
        # always ensure tracing is removed
        sys.settrace(None)

        conn.send({
            "snapshots": tracer.snapshots,
            "variable_history": tracer.variable_history,
            "line_index": tracer.line_index,
            "truncated": tracer.truncated,
            "error": error
        })

        conn.close()