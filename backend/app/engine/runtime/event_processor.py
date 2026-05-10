"""
Event Processor — the central pipeline between runtime hooks and snapshot storage.

Pipeline:  AST hooks  →  runtime handlers  →  EventProcessor  →  snapshots

The processor normalises raw events, applies mode-specific filtering,
compresses redundant entries, and finally dispatches accepted events
to the snapshot builder (EventLogger).

Modes plug in via an EventFilter protocol: each mode supplies a filter
that decides accept / reject / transform for every raw event.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol


# ── Filter protocol ─────────────────────────────────────────
class EventFilter(Protocol):
    """Each execution mode implements this to control what reaches snapshots."""

    def accept(self, event: Dict[str, Any]) -> bool:
        """Return True to keep the event, False to discard."""
        ...


# ── Built-in filters ────────────────────────────────────────
class AcceptAllFilter:
    """Detailed / smart mode — every event is kept."""

    def accept(self, event: Dict[str, Any]) -> bool:
        return True


class SemanticFilter:
    """Reduced mode — only meaningful state transitions survive.

    Kept events:
      • call, return  (always meaningful)
      • semantic       (explicitly injected algorithm events)
      • line           (only when delta is non-empty)
      • loop / while   (only first & last iteration, or when state changes)
      • if             (always — branch decision is meaningful)
      • break          (always — control flow shift)

    Discarded:
      • line events with empty delta
      • repetitive mid-loop iterations with no state change
      • continue events (usually noise)
    """

    def __init__(self):
        self._last_loop_line: Optional[int] = None

    def accept(self, event: Dict[str, Any]) -> bool:
        etype = event.get("event")

        # Always keep structural & semantic events
        if etype in ("call", "return", "semantic", "if", "break"):
            return True

        # Line events only if they carry a real state delta
        if etype == "line":
            return event.get("has_delta", False)

        # Loop / while: keep first iteration, iteration with state change,
        # and the exit evaluation (condition_result=False)
        if etype in ("loop", "while"):
            iteration = event.get("iteration", 0)
            value = event.get("value")
            # while-exit (condition became False)
            if etype == "while" and value is False:
                return True
            # first iteration
            if iteration == 0:
                return True
            # has meaningful state delta
            if event.get("has_delta", False):
                return True
            return False

        # continue: discard (noise)
        if etype == "continue":
            return False

        # Unknown event type — keep to be safe
        return True


# ── Processor ────────────────────────────────────────────────
class EventProcessor:
    """Normalise, filter, and compress events before they reach storage."""

    def __init__(self, event_filter: EventFilter | None = None):
        self.filter: EventFilter = event_filter or AcceptAllFilter()
        self._pending: List[Dict[str, Any]] = []

    def set_filter(self, f: EventFilter) -> None:
        self.filter = f

    # ── main entry ───────────────────────────────────────────
    def process(self, event: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Run the lightweight event through the pipeline.

        Returns (should_keep, event).
        """
        # 1. normalise — ensure required keys exist
        event.setdefault("has_delta", False)
        event.setdefault("explicit_delta", None)
        event.setdefault("value", None)
        event.setdefault("branch", None)
        event.setdefault("iteration", None)
        event.setdefault("loop_var", None)

        # 2. filter
        should_keep = self.filter.accept(event)

        # 3. (future) compression / batching hooks go here

        return should_keep, event
