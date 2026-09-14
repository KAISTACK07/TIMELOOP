"""Pydantic models for the Phase 7 AI Explainer endpoint (`POST /explain`).

The request carries *debugger context* — the code plus a snapshot of where the
user currently is in the replay timeline. The response is a structured analysis
that the frontend renders directly.

Design notes:
  * All secrets live server-side. Nothing here accepts or returns an API key.
  * `source` and `model` make the response honest: the UI can tell the user
    whether an explanation came from the LLM or the deterministic fallback,
    instead of always claiming "AI".
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# Hard input ceilings — a debugger context should never be huge, and these
# protect the prompt budget and the process from pathological payloads.
MAX_CODE_CHARS = 20_000
MAX_STACK_FRAMES = 200
MAX_VARIABLES = 300


class ExplainRequest(BaseModel):
    code: str = Field(default="", max_length=MAX_CODE_CHARS)
    current_line: int = 0
    snapshot: Optional[Dict[str, Any]] = None
    variables: Dict[str, Any] = {}
    stack: List[str] = []
    mode: str = "smart"


class ExplainResponse(BaseModel):
    # Kept camelCase to match the existing frontend (AIExplainerModal) with no
    # client changes required.
    timeComplexity: str = "O(n)"
    spaceComplexity: str = "O(1)"
    expectedComplexity: str = "O(n)"
    issue: str = ""
    optimization: str = ""
    optimizedCode: str = ""
    activeLineInfo: str = ""
    contextSummary: str = ""

    # Honesty metadata — added in Phase 7.
    source: str = "static-analysis"  # "llm" | "static-analysis"
    model: Optional[str] = None
    error: Optional[str] = None
