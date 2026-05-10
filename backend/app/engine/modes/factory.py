"""
Factory — thin compatibility shim.

Delegates to mode_router for the actual strategy selection.
Kept for backwards compatibility with ExecutionTracker imports.
"""

from .detailed_mode import DetailedMode
from .smart_mode import SmartMode
from .reduced_mode import ReducedMode


def get_mode_strategy(mode_str: str):
    mode_str = (mode_str or "smart").lower()
    if mode_str == "detailed":
        return DetailedMode()
    elif mode_str == "reduced":
        return ReducedMode()
    return SmartMode()
