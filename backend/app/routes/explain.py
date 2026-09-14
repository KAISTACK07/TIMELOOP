"""Phase 7 — secure backend AI Explainer route.

Replaces the old client-side heuristic. The frontend POSTs debugger context
here; the service decides between an LLM explanation and the deterministic
static analyzer. No API key ever touches the client.
"""

from fastapi import APIRouter

from app.models.explain import ExplainRequest, ExplainResponse
from app.engine.ai import explain as run_explain

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest):
    result = run_explain(payload.model_dump())
    return ExplainResponse(**result)
