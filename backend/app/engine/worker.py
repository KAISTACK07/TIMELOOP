import sys
from .tracer import Tracer
from .sandbox import get_sandbox_globals


def worker_main(code, conn):

    # import resource

    # resource.setrlimit(
    #     resource.RLIMIT_AS,
    #     (200 * 1024 * 1024, 200 * 1024 * 1024)
    # )

    tracer = Tracer()
    sandbox_globals = get_sandbox_globals()

    error = None

    try:
        # attach tracer
        sys.settrace(tracer.trace)

        # execute user code
        exec(code, sandbox_globals)

    except Exception as e:
        error = type(e).__name__ + ": " + str(e)

    finally:
        # stop tracing
        sys.settrace(None)

        conn.send({
            "snapshots": tracer.snapshots,
            "variable_history": tracer.variable_history,
            "truncated": tracer.truncated,
            "error": error
        })

        conn.close()