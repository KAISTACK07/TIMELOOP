import sys
from .tracer import Tracer
from .sandbox import get_sandbox_globals


def worker_main(code, conn):

    tracer = Tracer()
    sandbox_globals = get_sandbox_globals()

    error = None

    # attach tracer BEFORE execution
    sys.settrace(tracer.trace)

    try:
        exec(code, sandbox_globals, sandbox_globals)
    except Exception as e:
        error = type(e).__name__ + ": " + str(e)

    # detach tracer AFTER execution
    sys.settrace(None)

    # send results
    conn.send({
        "snapshots": tracer.snapshots,
        "variable_history": tracer.variable_history,
        "line_index": tracer.line_index,
        "truncated": tracer.truncated,
        "error": error
    })

    conn.close()