"""Phase 7 — AI Explainer.

`service.explain(...)` is the single entry point used by the `/explain` route.
It orchestrates: sanitize context -> (cache) -> try LLM -> fall back to the
deterministic AST static analyzer. No API key ever leaves this package.
"""

from .service import explain

__all__ = ["explain"]
