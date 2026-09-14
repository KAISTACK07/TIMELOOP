import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.execute import router as execute_router
from app.routes.explain import router as explain_router
from app.engine.ai import llm_client

app = FastAPI(title="TimeLoop Backend")

# CORS: default to permissive for local dev, but allow locking down in
# production via TIMELOOP_ALLOWED_ORIGINS (comma-separated).
_origins_env = os.environ.get("TIMELOOP_ALLOWED_ORIGINS", "*").strip()
allowed_origins = ["*"] if _origins_env in ("", "*") else [
    o.strip() for o in _origins_env.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Credentials cannot be combined with the "*" wildcard per the CORS spec.
    allow_credentials=allowed_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(execute_router)
app.include_router(explain_router)


@app.get("/")
def root():
    return {"message": "TimeLoop backend running"}


@app.get("/health")
def health():
    """Lightweight readiness probe (used later for observability, Phase 14)."""
    return {
        "status": "ok",
        "ai_explainer": "llm" if llm_client.is_configured() else "static-analysis",
    }