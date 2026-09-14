"""Tests for the Phase 7 AI Explainer (`/explain`).

These run without an API key: they exercise the deterministic static analyzer
and the route wiring. The LLM path is verified via a monkeypatched client so we
never make a network call in tests.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.engine.ai import static_analyzer, service, llm_client  # noqa: E402

client = TestClient(app)


# ── Static analyzer ──────────────────────────────────────────

def test_nested_loops_detected_as_quadratic():
    code = "for i in range(n):\n    for j in range(n):\n        x = i * j\n"
    a = static_analyzer.analyze(code)
    assert a["timeComplexity"] == "O(n²)"


def test_triple_nested_loop_is_cubic():
    code = (
        "for i in range(n):\n"
        "    for j in range(n):\n"
        "        for k in range(n):\n"
        "            pass\n"
    )
    a = static_analyzer.analyze(code)
    assert a["timeComplexity"] == "O(n^3)"


def test_recursion_detected():
    code = "def fib(n):\n    if n < 2:\n        return n\n    return fib(n-1) + fib(n-2)\n"
    a = static_analyzer.analyze(code)
    assert "recursion" in a["spaceComplexity"].lower()


def test_backtracking_detected():
    code = (
        "def solve(board):\n"
        "    for i in range(9):\n"
        "        board.append(i)\n"
        "        solve(board)\n"
        "        board.pop()\n"
    )
    a = static_analyzer.analyze(code)
    assert "exponential" in a["timeComplexity"].lower() or "b" in a["timeComplexity"]


def test_syntax_error_reported_honestly():
    a = static_analyzer.analyze("def broken(:\n")
    assert a["timeComplexity"] == "unknown"


def test_active_line_info():
    code = "a = 1\nb = 2\nc = 3\n"
    a = static_analyzer.analyze(code, current_line=2)
    assert "b = 2" in a["activeLineInfo"]


# ── Route ────────────────────────────────────────────────────

def test_explain_endpoint_returns_full_schema():
    resp = client.post(
        "/explain",
        json={
            "code": "for i in range(n):\n    for j in range(n):\n        pass\n",
            "current_line": 2,
            "mode": "smart",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "timeComplexity",
        "spaceComplexity",
        "expectedComplexity",
        "issue",
        "optimization",
        "optimizedCode",
        "source",
    ):
        assert key in body
    assert body["source"] in ("llm", "static-analysis")


def test_explain_endpoint_rejects_oversized_code():
    resp = client.post("/explain", json={"code": "x" * 20_001})
    assert resp.status_code == 422  # pydantic max_length


def test_health_reports_ai_mode():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["ai_explainer"] in ("llm", "static-analysis")


# ── LLM path (mocked) ────────────────────────────────────────

def test_llm_path_used_when_configured(monkeypatch):
    service._CACHE.clear()
    monkeypatch.setattr(llm_client, "is_configured", lambda: True)

    def fake_explain(ctx, timeout=30.0):
        return {
            "timeComplexity": "O(2^n)",
            "issue": "exponential recursion",
            "optimization": "memoize",
            "optimizedCode": "# optimized",
            "model": "claude-test",
        }

    monkeypatch.setattr(llm_client, "explain", fake_explain)
    out = service.explain({"code": "def f(n): return f(n-1)+f(n-2)", "mode": "smart"})
    assert out["source"] == "llm"
    assert out["timeComplexity"] == "O(2^n)"
    # static baseline back-fills fields the LLM omitted
    assert out["spaceComplexity"]


def test_llm_failure_falls_back_to_static(monkeypatch):
    service._CACHE.clear()
    monkeypatch.setattr(llm_client, "is_configured", lambda: True)

    def boom(ctx, timeout=30.0):
        raise RuntimeError("network down")

    monkeypatch.setattr(llm_client, "explain", boom)
    out = service.explain({"code": "for i in range(n):\n    pass", "mode": "smart"})
    assert out["source"] == "static-analysis"
    assert "AI unavailable" in (out["error"] or "")


if __name__ == "__main__":
    import subprocess

    raise SystemExit(subprocess.call(["pytest", "-q", __file__]))
