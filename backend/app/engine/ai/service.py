"""Orchestration for `POST /explain`.

Flow: sanitize -> cache lookup -> try LLM (if configured) -> merge over the
deterministic static analysis -> cache -> return.

The static analysis always runs and serves two purposes: it is the guaranteed
fallback, and it back-fills any field the LLM omitted (e.g. spaceComplexity).
So every response is complete regardless of which path produced it.
"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any, Dict, Optional

from app.models.explain import MAX_STACK_FRAMES, MAX_VARIABLES
from . import llm_client, static_analyzer

# Tiny in-process LRU cache keyed by the context hash. Avoids paying for
# repeated LLM calls when the user reopens the modal on the same step.
_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_CACHE_MAX = 128


def _sanitize(context: Dict[str, Any]) -> Dict[str, Any]:
    """Bound the untrusted context before it reaches a prompt or the analyzer."""
    variables = context.get("variables") or {}
    if isinstance(variables, dict) and len(variables) > MAX_VARIABLES:
        variables = dict(list(variables.items())[:MAX_VARIABLES])

    snapshot = context.get("snapshot") or None
    if isinstance(snapshot, dict):
        stack = snapshot.get("stack")
        if isinstance(stack, list) and len(stack) > MAX_STACK_FRAMES:
            snapshot = {**snapshot, "stack": stack[:MAX_STACK_FRAMES]}

    return {
        "code": str(context.get("code") or ""),
        "current_line": int(context.get("current_line") or 0),
        "snapshot": snapshot,
        "variables": variables if isinstance(variables, dict) else {},
        "stack": context.get("stack") or [],
        "mode": str(context.get("mode") or "smart"),
    }


def _cache_key(ctx: Dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "code": ctx["code"],
            "line": ctx["current_line"],
            "mode": ctx["mode"],
            "step": (ctx.get("snapshot") or {}).get("step"),
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return dict(_CACHE[key])
    return None


def _cache_put(key: str, value: Dict[str, Any]) -> None:
    _CACHE[key] = dict(value)
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)


def explain(context: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _sanitize(context)
    key = _cache_key(ctx)

    cached = _cache_get(key)
    if cached is not None:
        return cached

    # Deterministic baseline — always available, and used to back-fill LLM gaps.
    base = static_analyzer.analyze(
        ctx["code"], ctx["current_line"], ctx["snapshot"], ctx["variables"]
    )
    result: Dict[str, Any] = {**base, "source": "static-analysis", "model": None, "error": None}

    if llm_client.is_configured():
        try:
            llm = llm_client.explain(ctx)
            result = {**result, **llm, "source": "llm", "error": None}
        except Exception as exc:  # noqa: BLE001 — degrade to static, never 500
            result["source"] = "static-analysis"
            result["error"] = f"AI unavailable ({type(exc).__name__}); showing static analysis."

    _cache_put(key, result)
    return result
