"""
Smart Mode — structured AST-based tracing.

Provides structured execution tracing focused on meaningful state
transitions while preserving debugger correctness.  Unlike detailed
mode it does NOT try to replicate sys.settrace granularity; instead
it relies on AST instrumentation to capture assignments, control flow,
and function calls in a controlled manner.
"""

# Step ceiling prevents runaway event accumulation in the frontend
_SMART_MAX_STEPS = 5000


class SmartMode:
    """Strategy object for smart / AST-instrumented execution."""

    def should_log(self, step: int) -> bool:
        """Accept events up to the smart-mode ceiling."""
        return step < _SMART_MAX_STEPS
