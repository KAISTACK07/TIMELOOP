import time
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
        start_time = time.time()
        
        result = None
        while True:
            if parent_conn.poll(0.05):
                try:
                    result = parent_conn.recv()
                except EOFError:
                    pass
                break
                
            if time.time() - start_time > timeout:
                break
                
            if not process.is_alive():
                break

        if process.is_alive():
            process.terminate()
            process.join()  # ← CRITICAL

            if result is None:
                return {
                    "session_id": str(uuid.uuid4()),
                    "snapshots": [],
                    "variable_history": {},
                    "line_index": {},
                    "truncated": True,
                    "error": "Execution timeout",
                    "stdout": ""
                }

        process.join()
        
        if result is None:
            # Check one last time in case it exited and flushed simultaneously
            if parent_conn.poll():
                try:
                    result = parent_conn.recv()
                except EOFError:
                    pass

        if result is None:
            result = {
                "snapshots": [],
                "truncated": True,
                "error": "Worker terminated (memory limit or crash)",
                "stdout": ""
            }

        return {
            "session_id": str(uuid.uuid4()),
            "snapshots": result.get("snapshots", []),
            "variable_history": result.get("variable_history", {}),
            "line_index": result.get("line_index", {}),
            "function_calls": result.get("function_calls", []),
            "truncated": result.get("truncated", True),
            "error": result.get("error"),
            "stdout": result.get("stdout", "")
        }