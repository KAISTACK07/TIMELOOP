"""
Reduced Mode — semantic suppression for scalable execution tracing.

This mode is NOT "less accurate tracing" or "compressed Smart Mode."
It is fundamentally different: generic instrumentation (line, loop, if,
call, return) is SUPPRESSED at the handler level itself, so those hooks
become near-zero-cost no-ops.

The ONLY events that survive are:
  • __semantic_event__() calls explicitly placed in user code
  • The top-level call/return (entry and exit of the outermost function)

This allows exponential-recursion algorithms (N-Queens, Sudoku, etc.)
to execute at near-native speed while still emitting a meaningful
semantic timeline.
"""


class ReducedMode:
    """Strategy object for reduced / semantic execution.

    Provides a `suppress_generic` flag that ExecutionTracker checks
    to skip all generic instrumentation in the handler bodies.
    """

    suppress_generic = True

    def should_log(self, step: int) -> bool:
        """In reduced mode, only semantic events should be logged.

        Generic handlers check `suppress_generic` and early-return
        before ever reaching this method, so this is only called for
        semantic events — always return True.
        """
        return True
