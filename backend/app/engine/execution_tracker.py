"""
Execution Tracker — orchestrates AST-instrumented execution.

Wires together:
  • StackManager    – call stack & loop iteration tracking
  • StateManager    – variable delta computation & history
  • EventLogger     – snapshot storage (end of pipeline)
  • EventProcessor  – filtering / compression (middle of pipeline)
  • ExecutionLimits – global step & depth protection
  • SemanticLogger  – reduced-mode semantic event collection

The tracker exposes handler functions that are injected into the
sandbox namespace (__log__, __call__, __return__, etc.).  These
handlers emit *generic* events — mode-specific interpretation
happens inside the EventProcessor via its pluggable filter.

REDUCED MODE SUPPRESSION:
  When mode == "reduced", the mode_strategy has `suppress_generic = True`.
  All generic handlers become near-zero-cost no-ops:
    • handle_log        → immediate return (no scope, no limits)
    • handle_call       → push_depth only (stack overflow protection)
    • handle_return     → pop_depth only
    • handle_if_chain   → immediate return
    • handle_for        → yield from iterable (no per-item overhead)
    • handle_while_cond → return condition_value
    • handle_break/continue/loop_enter/loop_exit → immediate return

  The ONLY handler that records events is handle_semantic_event.
  The process-level EXECUTION_TIMEOUT is the safety net against
  infinite loops — no per-step limits needed in suppressed mode.
"""

from __future__ import annotations

import sys

from .runtime.stack_manager import StackManager
from .runtime.state_manager import StateManager
from .runtime.event_logger import EventLogger
from .runtime.event_processor import EventProcessor
from .runtime.execution_limits import ExecutionLimits
from .runtime.semantic_logger import SemanticLogger
from .runtime.semantic_summaries import get_summary
from .modes.factory import get_mode_strategy
from .modes.mode_router import get_event_filter


def safe_serialize(value):
    """Convert a Python value into a JSON-safe representation."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [safe_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(k): safe_serialize(v) for k, v in value.items()}
    if isinstance(value, set):
        return [safe_serialize(item) for item in value]
    return str(value)


class ExecutionTracker:
    def __init__(self, mode: str = "smart"):
        self.mode = mode
        self.mode_strategy = get_mode_strategy(mode)

        # ── suppression flag ─────────────────────────────────
        # True when mode == "reduced" — causes all generic handlers
        # to early-return with near-zero overhead.
        self._suppress = getattr(self.mode_strategy, "suppress_generic", False)

        # ── runtime modules ──────────────────────────────────
        self.stack = StackManager()
        self.state = StateManager()
        self.limits = ExecutionLimits()
        self.semantic = SemanticLogger()

        # ── event pipeline ───────────────────────────────────
        event_filter = get_event_filter(mode)
        self.processor = EventProcessor(event_filter)
        self.logger = EventLogger(self.stack, self.state, self.processor)

        # ── aggregation ──────────────────────────────────────
        self.line_index: dict = {}
        self.function_calls: list = []
        self._seen_exception_ids: set[int] = set()

    # ── gate ─────────────────────────────────────────────────
    def _should_log(self) -> bool:
        return self.mode_strategy.should_log(self.logger.step)

    def _check_limits(self) -> None:
        """Delegate step checking to centralised limits."""
        self.limits.check_step()

    # ══════════════════════════════════════════════════════════
    # HANDLERS (injected into sandbox namespace)
    # ══════════════════════════════════════════════════════════

    def handle_log(self, name: str, value, line_no: int):
        """Variable assignment event."""
        if self._suppress:
            return  # ← ZERO-COST: no scope, no limits, no event

        self._check_limits()
        self.stack.scopes[-1][name] = value

        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(line_no)
            accepted = self.logger.record(
                "line", exec_line, call_site_line=call_site,
            )
            if accepted:
                self.line_index.setdefault(line_no, []).append(self.logger.step - 1)

    def handle_call(self, func_name: str, args: tuple, kwargs: dict,
                    def_line_no: int, call_site_line: int, local_vars: dict | None = None):
        """Function call event.

        Parameter binding is the state transition owned by this event.

        Snapshot fields:
          - line_no       = the function's entry line (actual execution)
          - call_site_line = where the function was invoked
        """
        if self._suppress:
            return  # ← depth managed by call_wrapper in worker.py

        self._check_limits()
        scope = dict(local_vars) if local_vars else {}
        self.limits.push_depth()
        try:
            self.stack.push_frame(func_name, call_site_line, scope)
        except Exception:
            self.limits.pop_depth()
            raise

        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(def_line_no)
            accepted = self.logger.record(
                "call", exec_line, call_site_line=call_site,
            )
            if accepted:
                self.function_calls.append({
                    "name": func_name,
                    "line_no": def_line_no,
                    "call_site_line": call_site,
                    "step": self.logger.step - 1,
                })
                self.line_index.setdefault(def_line_no, []).append(self.logger.step - 1)

    def handle_return(self, name: str, value, line_no: int):
        """Function return event.

        Return values are owned exclusively by the return event.
        No duplicate __return__ line event is emitted.
        """
        if self._suppress:
            return  # ← depth managed by call_wrapper in worker.py

        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(line_no)
            accepted = self.logger.record(
                "return", exec_line,
                delta={},
                call_site_line=call_site,
                value=safe_serialize(value),
            )
            if accepted:
                self.line_index.setdefault(line_no, []).append(self.logger.step - 1)
        self.limits.pop_depth()
        self.stack.pop_frame()

    def _resolve_exception_line(self, exc: BaseException, fallback_line: int) -> int:
        tb = exc.__traceback__
        last_sandbox_line = None
        while tb is not None:
            frame = tb.tb_frame
            if frame.f_code.co_filename == "<sandbox>":
                last_sandbox_line = tb.tb_lineno
            tb = tb.tb_next
        return last_sandbox_line or fallback_line

    def handle_exception(self, func_name: str, exc: BaseException, fallback_line: int, call_site_line: int | None = None):
        """Record the first semantic exception event for a propagated exception object."""
        if self._suppress:
            return

        exc_id = id(exc)
        if exc_id in self._seen_exception_ids:
            return
        self._seen_exception_ids.add(exc_id)

        line_no = self._resolve_exception_line(exc, fallback_line)
        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(line_no)
            stack_snapshot = list(self.stack.call_stack)
            if not stack_snapshot or stack_snapshot[-1] != func_name:
                if stack_snapshot:
                    stack_snapshot = stack_snapshot + [func_name]
                else:
                    stack_snapshot = ["global", func_name]
            accepted = self.logger.record(
                "exception",
                exec_line,
                delta={},
                call_site_line=call_site_line if call_site_line is not None else call_site,
                value={
                    "exception_type": type(exc).__name__,
                    "message": str(exc),
                },
                function_override=func_name,
                stack_override=stack_snapshot,
                locals_override={},
            )
            if accepted:
                self.line_index.setdefault(line_no, []).append(self.logger.step - 1)

    def handle_exception_unwind(self, line_no: int | None = None, func_name: str | None = None, call_site_line: int | None = None):
        """Called by worker.py when an exception bypasses normal return."""
        if self._suppress:
            return
        active_func = func_name or self.stack.call_stack[-1]
        if self._should_log():
            unwind_line = line_no if line_no is not None else (self.stack.call_lines[-1] if self.stack.call_lines else 0)
            exec_line, call_site = self.stack.get_execution_line(unwind_line)
            stack_snapshot = list(self.stack.call_stack)
            if not stack_snapshot or stack_snapshot[-1] != active_func:
                if stack_snapshot:
                    stack_snapshot = stack_snapshot + [active_func]
                else:
                    stack_snapshot = ["global", active_func]
            accepted = self.logger.record(
                "exception_unwind",
                exec_line,
                delta={},
                call_site_line=call_site_line if call_site_line is not None else call_site,
                function_override=active_func,
                stack_override=stack_snapshot,
                locals_override={},
            )
            if accepted and unwind_line:
                self.line_index.setdefault(unwind_line, []).append(self.logger.step - 1)
        self.limits.pop_depth()
        self.stack.pop_frame()

    def handle_if_chain(self, branch_name: str, internal_line: int, line_no: int):
        """If/elif/else branch evaluation event."""
        if self._suppress:
            return  # ← ZERO-COST

        self._check_limits()
        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(internal_line)
            if not call_site:
                exec_line = internal_line
            value = branch_name in ("then", "elif")
            accepted = self.logger.record(
                "if", exec_line,
                delta={},
                call_site_line=call_site,
                value=value,
                branch=branch_name,
            )
            if accepted:
                self.line_index.setdefault(line_no, []).append(self.logger.step - 1)

    # ── loop handlers ────────────────────────────────────────

    def handle_loop_enter(self):
        """Push a new loop context onto the stack."""
        if self._suppress:
            return
        self.stack.push_loop()

    def handle_loop_exit(self):
        """Pop the current loop context."""
        if self._suppress:
            return
        self.stack.pop_loop()

    def handle_for(self, iterable, line_no: int, target_names: list | None = None):
        """For-loop iteration generator — yields items while logging."""
        if self._suppress:
            # ← REDUCED MODE: pure passthrough, no per-item overhead
            yield from iterable
            return

        for idx, item in enumerate(iterable):
            self._check_limits()
            self.stack.update_loop_iter(idx)

            # Build loop_var: map target names to their values
            loop_var = {}
            if target_names:
                if len(target_names) == 1:
                    loop_var[target_names[0]] = safe_serialize(item)
                else:
                    try:
                        for i, name in enumerate(target_names):
                            loop_var[name] = safe_serialize(item[i])
                    except (IndexError, TypeError):
                        loop_var[target_names[0]] = safe_serialize(item)

            if self._should_log():
                exec_line, call_site = self.stack.get_execution_line(line_no)
                accepted = self.logger.record(
                    "loop", exec_line,
                    call_site_line=call_site,
                    iteration=idx,
                    loop_var=loop_var,
                )
                if accepted:
                    self.line_index.setdefault(line_no, []).append(self.logger.step - 1)
            yield item

    def handle_while_cond(self, condition_value, line_no: int):
        """While-loop condition evaluation — logs every check including exit."""
        if self._suppress:
            return condition_value  # ← ZERO-COST

        self._check_limits()
        # Deferred advance: if a body ran since the last check, bump iter now
        current_iter = self.stack.advance_while_iter_if_needed()
        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(line_no)
            accepted = self.logger.record(
                "while", exec_line,
                call_site_line=call_site,
                value=safe_serialize(condition_value),
                iteration=current_iter,
            )
            if accepted:
                self.line_index.setdefault(line_no, []).append(self.logger.step - 1)
        if condition_value:
            self.stack.mark_while_body_entered()
        return condition_value

    def handle_break(self, line_no: int):
        """Break statement event."""
        if self._suppress:
            return

        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(line_no)
            accepted = self.logger.record(
                "break", exec_line,
                delta={},
                call_site_line=call_site,
                iteration=self.stack.get_current_loop_iter(),
            )
            if accepted:
                self.line_index.setdefault(line_no, []).append(self.logger.step - 1)

    def handle_continue(self, line_no: int):
        """Continue statement event."""
        if self._suppress:
            return

        if self._should_log():
            exec_line, call_site = self.stack.get_execution_line(line_no)
            accepted = self.logger.record(
                "continue", exec_line,
                delta={},
                call_site_line=call_site,
                iteration=self.stack.get_current_loop_iter(),
            )
            if accepted:
                self.line_index.setdefault(line_no, []).append(self.logger.step - 1)

    # ══════════════════════════════════════════════════════════
    # SEMANTIC AGGREGATION ENGINE
    # ══════════════════════════════════════════════════════════
    #
    # Aggregation collapses consecutive same-type events into
    # summaries.  For alternating patterns (Sudoku), a sampling
    # gate ensures only a bounded number of small windows emit.
    #
    # Cost per event in hot path: ~2 integer ops + 1 string cmp.
    # Frame introspection has been entirely replaced by AST-injected
    # __line__ and __func__ kwargs.

    _HIGH_PRIORITY = frozenset({
        "solution_found", "solved", "function_entry", "function_complete",
        "execution_complete",
    })

    _MAX_SEMANTIC_EVENTS = 500

    def _init_aggregation(self):
        if hasattr(self, "_agg_name"):
            return
        self._agg_name = None
        self._agg_count = 0
        self._agg_first_data = None
        self._agg_line = 0
        self._agg_func = "global"
        self._sem_emitted = 0
        self._sem_total_seen = 0
        self._sem_counts = {}
        
        # Deduplication state
        self._last_event_name = None
        self._last_event_data = None
        self._last_event_func = None

    def _emit_snapshot(self, event_name, data, line_no, func_name,
                       aggregated=False, count=1):
        if self._sem_emitted >= self._MAX_SEMANTIC_EVENTS:
            return
        serialized = safe_serialize(data) if data else {}
        step = self.logger.step
        value = {"name": event_name, "data": serialized}
        if aggregated:
            value["aggregated"] = True
            value["count"] = count
            value["summary"] = get_summary(event_name, count)
        self.logger.snapshots.append({
            "step": step, "event": "semantic", "line_no": line_no,
            "call_site_line": None, "function": func_name,
            "stack": [func_name], "locals": {}, "delta": {},
            "value": value, "branch": None, "iteration": None,
            "loop_var": None, "is_full": True,
        })
        self.logger.step += 1
        self._sem_emitted += 1
        if line_no:
            self.line_index.setdefault(line_no, []).append(step)

    def _flush_aggregation(self):
        if self._agg_name is None:
            return
        name, count = self._agg_name, self._agg_count
        line, func = self._agg_line, self._agg_func

        if count > 3:
            # Large run → always emit aggregated summary
            self._emit_snapshot(name, {"count": count}, line, func,
                                aggregated=True, count=count)
        else:
            # Small run → sampling gate: only emit first few of each type
            total = self._sem_counts.get(name, 0)
            if total <= 5 or (total <= 50 and total % 10 == 0) or total % 50 == 0:
                self._emit_snapshot(name, self._agg_first_data, line, func)
            # else: silently drop — this type is too frequent

        self._agg_name = None
        self._agg_count = 0
        self._agg_first_data = None

    def handle_semantic_event(self, event_name, data=None, __line__=0, __func__="global", **kwargs):
        """Semantic event with aggregation + sampling.

        Hot path cost: ~2 integer ops + 1 string comparison.
        No sys._getframe, no safe_serialize, no dict construction
        on the hot path. Static __line__ and __func__ provided by AST.
        """
        self._init_aggregation()
        
        # Deduplicate identical consecutive events
        if event_name == self._last_event_name and data == self._last_event_data and __func__ == self._last_event_func:
            return
            
        self._last_event_name = event_name
        self._last_event_data = data
        self._last_event_func = __func__

        self._sem_total_seen += 1
        self._sem_counts[event_name] = self._sem_counts.get(event_name, 0) + 1

        # HIGH priority: flush + emit immediately
        if event_name in self._HIGH_PRIORITY:
            self._flush_aggregation()
            self.semantic.record(event_name, data, __line__)
            self._emit_snapshot(event_name, data, __line__, __func__)
            return

        # Hard cap
        if self._sem_emitted >= self._MAX_SEMANTIC_EVENTS:
            return

        # Same type as current window: just increment (cheapest path)
        if event_name == self._agg_name:
            self._agg_count += 1
            return  # ← NO data storage, NO frame, NO serialize

        # Different type: flush previous window, start new
        self._flush_aggregation()
        self._agg_name = event_name
        self._agg_count = 1
        self._agg_first_data = data
        self._agg_line = __line__
        self._agg_func = __func__
        self.semantic.record(event_name, data, __line__)

    def get_response(self):
        if hasattr(self, "_agg_name"):
            self._flush_aggregation()
        compression = None
        if hasattr(self, "_sem_total_seen") and self._sem_total_seen > self._sem_emitted:
            compression = {
                "total_seen": dict(getattr(self, "_sem_counts", {})),
                "total_emitted": self._sem_emitted,
                "suppressed": self._sem_total_seen - self._sem_emitted,
            }
        return {
            "snapshots": self.logger.snapshots,
            "variable_history": self.state.variable_history,
            "line_index": self.line_index,
            "function_calls": self.function_calls,
            "truncated": self.limits.is_truncated,
            "compression": compression,
            "error": None,
        }
