"""
Event Logger — final snapshot storage at the end of the event pipeline.

Raw events arrive from runtime hooks, pass through the EventProcessor
(filtering / compression), and land here for persistent storage.

Snapshot schema:
  - line_no:        actual source line being executed
  - call_site_line: line where enclosing function was invoked (None at global)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .stack_manager import StackManager
from .state_manager import StateManager
from .event_processor import EventProcessor


class EventLogger:
    def __init__(self, stack_manager: StackManager, state_manager: StateManager,
                 event_processor: EventProcessor | None = None):
        self.stack = stack_manager
        self.state = state_manager
        self.processor = event_processor or EventProcessor()
        self.snapshots: List[Dict[str, Any]] = []
        self.step: int = 1

    def record(
        self,
        event_type: str,
        line_no: int,
        *,
        delta: dict | None = None,
        call_site_line: int | None = None,
        value: Any = None,
        branch: str | None = None,
        iteration: int | None = None,
        loop_var: dict | None = None,
        function_override: str | None = None,
        stack_override: list[str] | None = None,
        locals_override: dict | None = None,
    ) -> bool:
        """Build a raw lightweight event and send it through the processor pipeline.
        Only builds the heavy snapshot and commits the state delta if accepted.

        Returns True if the event was accepted into snapshots, False if filtered.
        """
        if delta is not None:
            has_delta = bool(delta)
        else:
            has_delta = self.state.has_delta(self.stack.scopes[-1])

        lightweight_event = {
            "event": event_type,
            "line_no": line_no,
            "has_delta": has_delta,
            "explicit_delta": delta,
            "value": value,
            "branch": branch,
            "iteration": iteration,
            "loop_var": loop_var,
        }

        # ── run through event processor ─────────────────────
        should_keep, normalized = self.processor.process(lightweight_event)
        
        if not should_keep:
            # Event was filtered out — still bump step so IDs stay unique
            self.step += 1
            return False

        # Only now do we compute the actual deepcopy delta, since we are keeping it!
        final_delta = normalized["explicit_delta"]
        if final_delta is None:
            final_delta = self.state.compute_delta(self.stack.scopes[-1]) if normalized["has_delta"] else {}

        # Build full heavy snapshot only for kept events
        full_event = {
            "step": self.step,
            "event": normalized["event"],
            "line_no": normalized["line_no"],
            "call_site_line": call_site_line,
            "function": function_override if function_override is not None else self.stack.call_stack[-1],
            "stack": list(stack_override) if stack_override is not None else list(self.stack.call_stack),
            "locals": dict(locals_override) if locals_override is not None else dict(self.stack.scopes[-1]),
            "delta": final_delta,
            "value": normalized["value"],
            "branch": normalized["branch"],
            "iteration": normalized["iteration"],
            "loop_var": normalized["loop_var"],
            "is_full": True,
        }

        self.snapshots.append(full_event)
        
        # Commit delta to variable history ONLY for kept events
        if final_delta:
            self.state.commit_delta(final_delta, self.step)

        self.step += 1
        return True
