import uuid
from multiprocessing import Process, Pipe

from .worker import worker_main
from .limits import EXECUTION_TIMEOUT


class ExecutionEngine:

    def run(self, code: str):

        parent_conn, child_conn = Pipe()

        process = Process(
            target=worker_main,
            args=(code, child_conn)
        )

        process.start()

        process.join(EXECUTION_TIMEOUT)

        if process.is_alive():
            process.terminate()

            return {
                "session_id": str(uuid.uuid4()),
                "snapshots": [],
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
            "truncated": result.get("truncated", True),
            "error": result.get("error")
        }