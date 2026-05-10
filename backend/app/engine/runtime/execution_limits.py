"""
Centralized execution limits — applied globally across ALL modes.

This is the single source of truth for step counts, recursion depth,
and timeout thresholds.  Individual runtime hooks (while, for, etc.)
must NOT implement their own protection; they delegate to this module.
"""

from ..limits import MAX_STEPS, MAX_DEPTH


class ExecutionLimits:
    """Track step count & recursion depth; raise on violation."""

    def __init__(self, max_steps: int = MAX_STEPS, max_depth: int = MAX_DEPTH):
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.current_step: int = 0
        self.current_depth: int = 0
        self.truncated: bool = False

    # ── step gate ────────────────────────────────────────────
    def check_step(self) -> None:
        """Increment step counter and raise if limit exceeded."""
        self.current_step += 1
        if self.current_step >= self.max_steps:
            self.truncated = True
            raise StopIteration("Max execution steps exceeded")

    # ── depth gate ───────────────────────────────────────────
    def push_depth(self) -> None:
        """Called on function call / recursion entry."""
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.truncated = True
            raise StopIteration("Max call depth exceeded")

    def pop_depth(self) -> None:
        """Called on function return."""
        if self.current_depth > 0:
            self.current_depth -= 1

    # ── query ────────────────────────────────────────────────
    @property
    def is_truncated(self) -> bool:
        return self.truncated
