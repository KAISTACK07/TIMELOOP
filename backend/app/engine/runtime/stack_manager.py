from typing import List, Dict, Any, Tuple


class StackManager:
    def __init__(self):
        self.call_stack: List[str] = ["global"]
        self.call_lines: List[int] = []
        self.loop_iters: List[int] = []
        self.scopes: List[Dict[str, Any]] = [{}]
        # Track whether each loop's body has executed at least once.
        # Used to advance while-loop iteration at the START of the
        # next condition check instead of at the end of the previous one,
        # so that break/continue see the same iteration as the while event.
        self._loop_needs_advance: List[bool] = []

    def push_frame(self, name: str, line_no: int, scope: Dict[str, Any]):
        self.call_stack.append(name)
        self.call_lines.append(line_no)
        self.scopes.append(scope)

    def pop_frame(self):
        if len(self.call_stack) > 1:
            self.call_stack.pop()
            self.call_lines.pop()
            self.scopes.pop()

    def push_loop(self):
        self.loop_iters.append(0)
        self._loop_needs_advance.append(False)

    def pop_loop(self):
        if self.loop_iters:
            self.loop_iters.pop()
        if self._loop_needs_advance:
            self._loop_needs_advance.pop()

    def get_current_loop_iter(self) -> int:
        return self.loop_iters[-1] if self.loop_iters else 0

    def update_loop_iter(self, idx: int):
        """Set iteration explicitly (used by for-loops)."""
        if self.loop_iters:
            self.loop_iters[-1] = idx

    def advance_while_iter_if_needed(self) -> int:
        """Advance the while-loop iteration counter if a previous body ran.

        Called at the START of each while-condition evaluation.
        Returns the iteration index to use for this evaluation.
        """
        if self.loop_iters and self._loop_needs_advance:
            if self._loop_needs_advance[-1]:
                self.loop_iters[-1] += 1
            return self.loop_iters[-1]
        return 0

    def mark_while_body_entered(self):
        """Mark that the current while-loop body is about to execute.

        The next condition evaluation will advance the counter.
        """
        if self._loop_needs_advance:
            self._loop_needs_advance[-1] = True

    def increment_loop_iter(self):
        """Legacy: direct increment (kept for any edge cases)."""
        if self.loop_iters:
            self.loop_iters[-1] += 1

    def get_execution_line(self, source_line_no: int) -> Tuple[int, int | None]:
        """Return (execution_line, call_site_line).

        - execution_line:  the actual source line being executed (always source_line_no)
        - call_site_line:  where the enclosing function was invoked from (None at global)
        """
        if len(self.call_lines) > 0:
            return source_line_no, self.call_lines[-1]
        return source_line_no, None
