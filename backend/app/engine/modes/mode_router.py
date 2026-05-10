"""
Mode Router — centralised dispatch for execution modes.

Responsibilities:
  1. Select the correct execution strategy based on mode string.
  2. Configure the event processor with the appropriate filter.
  3. Guarantee a uniform API response schema across ALL modes.
"""

from __future__ import annotations

from typing import Any, Dict

from ..runtime.event_processor import AcceptAllFilter, SemanticFilter


# ── Mode definitions ─────────────────────────────────────────

VALID_MODES = {"detailed", "smart", "reduced"}


def get_event_filter(mode: str):
    """Return the correct EventFilter for the given mode.

    - detailed / smart → AcceptAllFilter (keep everything)
    - reduced          → SemanticFilter  (semantic only)
    """
    if mode == "reduced":
        return SemanticFilter()
    return AcceptAllFilter()


def get_execution_strategy(mode: str) -> str:
    """Decide the execution back-end for a mode.

    Returns:
        'settrace'  — use sys.settrace (detailed mode)
        'ast'       — use AST instrumentation (smart / reduced)
    """
    if mode == "detailed":
        return "settrace"
    return "ast"


def normalise_mode(mode: str) -> str:
    """Clamp an unknown mode string to a valid default."""
    mode = (mode or "smart").lower()
    return mode if mode in VALID_MODES else "smart"


# ── Response schema ──────────────────────────────────────────

def build_response(
    *,
    session_id: str = "",
    snapshots: list | None = None,
    variable_history: dict | None = None,
    line_index: dict | None = None,
    function_calls: list | None = None,
    truncated: bool = False,
    error: str | None = None,
) -> Dict[str, Any]:
    """Build a guaranteed-shape API response dict."""
    return {
        "session_id": session_id,
        "snapshots": snapshots or [],
        "variable_history": variable_history or {},
        "line_index": line_index or {},
        "function_calls": function_calls or [],
        "truncated": truncated,
        "error": error,
    }
