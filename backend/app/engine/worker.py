"""
Worker — isolated process entry point for code execution.

Supports three modes:
  - detailed: sys.settrace (full frame tracing)
  - smart:    AST instrumentation (structured state transitions)
  - reduced:  AST instrumentation + semantic event filtering
"""

import sys
import inspect
import pickle

from .tracer import Tracer
from .sandbox import get_sandbox_globals
from .ast_instrumenter import instrument_code
from .execution_tracker import ExecutionTracker
from .modes.mode_router import normalise_mode, get_execution_strategy, build_response


def _to_transport_safe(value):
    """Preserve native built-in structures; degrade only non-picklable objects."""
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if isinstance(value, list):
        return [_to_transport_safe(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_to_transport_safe(v) for v in value)
    if isinstance(value, set):
        return {_to_transport_safe(v) for v in value}
    if isinstance(value, dict):
        return {k: _to_transport_safe(v) for k, v in value.items()}
    try:
        pickle.dumps(value)
        return value
    except Exception:
        return repr(value)


def worker_main(code, conn, mode):

    mode = normalise_mode(mode)
    strategy = get_execution_strategy(mode)
    sandbox_globals = get_sandbox_globals()

    # In reduced mode, we rely on Python's own recursion limit instead
    # of per-step tracking. Raise it to handle deep backtracking algorithms.
    if mode == "reduced":
        sys.setrecursionlimit(10000)

    error = None
    snapshots = []
    variable_history = {}
    line_index = {}
    function_calls = []
    truncated = False

    try:
        # ──────────────────────────────────────────────
        # 🔴 DETAILED MODE → sys.settrace (unchanged)
        # ──────────────────────────────────────────────
        if strategy == "settrace":
            tracer = Tracer(mode=mode)
            sys.settrace(tracer.trace)
            exec(code, sandbox_globals, sandbox_globals)
            sys.settrace(None)

            snapshots = tracer.snapshots
            variable_history = tracer.variable_history
            line_index = tracer.line_index
            truncated = tracer.truncated

        # ──────────────────────────────────────────────
        # 🟡 SMART / 🟢 REDUCED → AST instrumentation
        # ──────────────────────────────────────────────
        else:
            tracker = ExecutionTracker(mode=mode)

            # Transform code → instrumented AST → compiled bytecode
            # In reduced mode, only functions with __semantic_event__
            # calls are instrumented — helpers run as native Python.
            compiled = instrument_code(code, mode=mode)

            # Define a robust execution wrapper for ALL function calls
            safe_builtins = sandbox_globals.get("__builtins__", {})
            safe_builtin_vals = list(safe_builtins.values()) if isinstance(safe_builtins, dict) else []

            # ── REDUCED MODE: zero-cost wrapper ─────────────
            if mode == "reduced":
                # O(1) builtin check instead of O(n) list scan
                _builtin_ids = {id(v) for v in safe_builtin_vals}
                _handle_semantic = tracker.handle_semantic_event

                def call_wrapper(__name, __call_site_line, __func, /, *args, **kwargs):
                    # No depth tracking, no try/finally, no handle_call.
                    # Python's own recursion limit + process timeout are
                    # the safety nets. This makes EVERY function call
                    # (including is_valid, find_empty, etc.) near-free.
                    return __func(*args, **kwargs)

                # Semantic event wrapper: injects the call_site_line from
                # the __call__ AST node so we avoid sys._getframe() overhead.
                # __semantic_event__ is a regular function call, so the AST
                # instrumenter wraps it: __call__("__semantic_event__", LINE, ...)
                # But since call_wrapper just calls func() directly, we need
                # the semantic wrapper itself to be injected with the line.
                # Since __semantic_event__ is called directly by user code
                # (not via __call__ because it starts with __), we capture
                # the line from the caller's code object at call time — but
                # only for the rare semantic events, not hot-path calls.
                def semantic_event_wrapper(event_name, data=None, **kwargs):
                    _handle_semantic(event_name, data, **kwargs)

            # ── SMART MODE: full introspection wrapper ───────
            else:
                def call_wrapper(__name, __call_site_line, __func, /, *args, **kwargs):
                    is_user_func = (inspect.isfunction(__func) or inspect.ismethod(__func) or inspect.isclass(__func)) and __func not in safe_builtin_vals

                    local_vars = {}
                    def_line_no = __call_site_line
                    if is_user_func:
                        try:
                            sig = inspect.signature(__func)
                            bound_args = sig.bind(*args, **kwargs)
                            bound_args.apply_defaults()
                            local_vars = dict(bound_args.arguments)
                            if hasattr(__func, "__code__"):
                                def_line_no = __func.__code__.co_firstlineno
                        except Exception:
                            pass  # Builtins or unsupported callables

                        tracker.handle_call(__name, args, kwargs, def_line_no, __call_site_line, local_vars)

                    success = False
                    pending_exception = None
                    try:
                        res = __func(*args, **kwargs)
                        success = True
                        return res
                    except BaseException as exc:
                        pending_exception = exc
                        if is_user_func:
                            tracker.handle_exception(__name, exc, def_line_no, __call_site_line)
                        raise
                    finally:
                        if is_user_func and not success:
                            unwind_line = def_line_no
                            if pending_exception is not None and pending_exception.__traceback__ is not None:
                                tb = pending_exception.__traceback__
                                while tb.tb_next is not None:
                                    tb = tb.tb_next
                                if tb.tb_frame.f_code.co_filename == "<sandbox>":
                                    unwind_line = tb.tb_lineno
                            tracker.handle_exception_unwind(
                                unwind_line,
                                func_name=__name,
                                call_site_line=__call_site_line,
                            )

                semantic_event_wrapper = tracker.handle_semantic_event

            # Inject tracking hooks into the execution namespace
            sandbox_globals["__log__"] = tracker.handle_log
            sandbox_globals["__call__"] = call_wrapper
            sandbox_globals["__return__"] = tracker.handle_return
            sandbox_globals["__log_if_chain__"] = tracker.handle_if_chain
            sandbox_globals["__loop_enter__"] = tracker.handle_loop_enter
            sandbox_globals["__loop_exit__"] = tracker.handle_loop_exit
            sandbox_globals["__for__"] = tracker.handle_for
            sandbox_globals["__while_cond__"] = tracker.handle_while_cond
            sandbox_globals["__break__"] = tracker.handle_break
            sandbox_globals["__continue__"] = tracker.handle_continue
            sandbox_globals["__semantic_event__"] = semantic_event_wrapper

            exec(compiled, sandbox_globals, sandbox_globals)

            result = tracker.get_response()
            snapshots = result["snapshots"]
            variable_history = result["variable_history"]
            line_index = result["line_index"]
            function_calls = result["function_calls"]
            truncated = result["truncated"]

    except StopIteration:
        truncated = True
        if strategy == "settrace" and 'tracer' in locals():
            snapshots = tracer.snapshots
            variable_history = tracer.variable_history
            line_index = tracer.line_index
        elif 'tracker' in locals():
            result = tracker.get_response()
            snapshots = result["snapshots"]
            variable_history = result["variable_history"]
            line_index = result["line_index"]
            function_calls = result["function_calls"]

    except Exception as e:
        error = type(e).__name__ + ": " + str(e)
        # Preserve whatever we collected before the error
        if strategy == "settrace" and 'tracer' in locals():
            snapshots = tracer.snapshots
            variable_history = tracer.variable_history
            line_index = tracer.line_index
        elif 'tracker' in locals():
            result = tracker.get_response()
            snapshots = result["snapshots"]
            variable_history = result["variable_history"]
            line_index = result["line_index"]
            function_calls = result["function_calls"]

    finally:
        sys.settrace(None)
        conn.send(_to_transport_safe({
            "snapshots": snapshots,
            "variable_history": variable_history,
            "line_index": line_index,
            "function_calls": function_calls,
            "truncated": truncated,
            "error": error
        }))
        conn.close()
