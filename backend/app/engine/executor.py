import uuid
from multiprocessing import Process, Pipe

from .worker import worker_main
from .limits import get_timeout
from .modes.mode_router import normalise_mode


class ExecutionEngine:

    def run(self, code: str, mode: str = "smart"):
        mode = normalise_mode(mode)

        parent_conn, child_conn = Pipe()

        process = Process(
            target=worker_main,
            args=(code, child_conn, mode)
        )

        process.start()

        timeout = get_timeout(mode)
        process.join(timeout)

        if process.is_alive():
            process.terminate()
            process.join()  # ← CRITICAL

            return {
                "session_id": str(uuid.uuid4()),
                "snapshots": [],
                "variable_history": {},
                "line_index": {},
                "truncated": True,
                "error": "Execution timeout"
            }

        if parent_conn.poll():
            result = parent_conn.recv()
        else:
            result = {
                "snapshots": [],
                "truncated": True,
                "error": "Worker terminated (memory limit or crash)"
            }

        return {
            "session_id": str(uuid.uuid4()),
            "snapshots": result.get("snapshots", []),
            "variable_history": result.get("variable_history", {}),
            "line_index": result.get("line_index", {}),
            "function_calls": result.get("function_calls", []),
            "truncated": result.get("truncated", True),
            "error": result.get("error")
}