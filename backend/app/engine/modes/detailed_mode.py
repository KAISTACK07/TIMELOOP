"""
Detailed Mode — maximum-granularity execution via sys.settrace.

This mode wraps the legacy Tracer and does NOT use AST instrumentation.
Every frame event (line, call, return, exception) is recorded.
"""


class DetailedMode:
    """Strategy object for detailed / settrace execution."""

    def should_log(self, step: int) -> bool:
        """Detailed mode logs everything unconditionally."""
        return True
