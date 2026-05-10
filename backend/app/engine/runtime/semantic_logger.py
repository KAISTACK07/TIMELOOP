"""
Semantic Logger — records high-level algorithm state transitions.

This is the runtime companion for reduced mode.  User code (or future
auto-detection) injects semantic events via __semantic_event__().
The logger stores them for the event processor to include in snapshots.

Semantic events are NOT tied to any specific algorithm; they are a
generic key/value protocol:

    __semantic_event__("queen_placed", {"row": 3, "col": 5})
    __semantic_event__("solution_found", {"board": [...]})

The AST layer NEVER calls this directly — it stays generic.
"""

from __future__ import annotations

from typing import Any, Dict, List


class SemanticLogger:
    """Collect and expose semantic events for reduced-mode tracing."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def record(self, event_name: str, data: Dict[str, Any] | None = None,
               line_no: int = 0) -> None:
        """Record a semantic event emitted by user code or runtime."""
        self.events.append({
            "semantic_name": event_name,
            "data": data or {},
            "line_no": line_no,
        })

    def pop_pending(self) -> List[Dict[str, Any]]:
        """Return and clear any pending semantic events."""
        pending = list(self.events)
        self.events.clear()
        return pending
