r"""Deterministic complexity analysis using Python's AST + runtime trace evidence.

This is the server-side replacement for the old client-side regex heuristic
(`generateClientAnalysis` in the frontend). It is *always* available — no
network, no API key — and is used both as the LLM fallback and as a structured
prior that is fed to the LLM.

Why AST beats regex:
  * Loop nesting depth is computed from real structure, not a fragile
    `for.*\n\s+for` pattern that misses `while`, comprehensions, and helpers.
  * Recursion is detected by resolving call names to enclosing function defs.
  * We fold in runtime evidence from the trace (step count, max stack depth)
    so the estimate reflects what actually happened, not just what could.
"""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional


class _Analysis:
    def __init__(self) -> None:
        self.max_loop_depth = 0
        self.has_recursion = False
        self.has_comprehension = False
        self.has_backtracking = False
        self.has_memoization = False
        self.function_names: List[str] = []


def _scan(tree: ast.AST) -> _Analysis:
    a = _Analysis()

    # Collect top-level + nested function names first, for recursion detection.
    func_defs: Dict[str, ast.FunctionDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_defs[node.name] = node
            a.function_names.append(node.name)

    # Recursion: a function whose body calls its own name.
    for name, fn in func_defs.items():
        for inner in ast.walk(fn):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Name)
                and inner.func.id == name
            ):
                a.has_recursion = True
                break
        if a.has_recursion:
            break

    # Max loop-nesting depth (for / while), computed recursively.
    def loop_depth(node: ast.AST, depth: int) -> int:
        best = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                best = max(best, loop_depth(child, depth + 1))
            else:
                best = max(best, loop_depth(child, depth))
        return best

    a.max_loop_depth = loop_depth(tree, 0)

    for node in ast.walk(tree):
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            a.has_comprehension = True
        # Backtracking signature: mutating a shared structure then undoing it.
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"pop", "remove", "discard"}:
                a.has_backtracking = True
        # Memoization signals.
        if isinstance(node, ast.Name) and node.id in {"lru_cache", "cache"}:
            a.has_memoization = True
        if isinstance(node, ast.Attribute) and node.attr in {"lru_cache", "cache"}:
            a.has_memoization = True

    return a


def _runtime_evidence(snapshot: Optional[Dict[str, Any]]) -> Dict[str, int]:
    stack = (snapshot or {}).get("stack") or []
    return {
        "stack_depth": len(stack) if isinstance(stack, list) else 0,
        "step": int((snapshot or {}).get("step") or 0),
    }


def analyze(
    code: str,
    current_line: int = 0,
    snapshot: Optional[Dict[str, Any]] = None,
    variables: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return the structured analysis dict (camelCase keys for the frontend)."""
    variables = variables or {}
    lines = (code or "").split("\n")
    active_line = ""
    if current_line and 1 <= current_line <= len(lines):
        active_line = f"Line {current_line}: {lines[current_line - 1].strip()}"

    evidence = _runtime_evidence(snapshot)

    try:
        tree = ast.parse(code or "")
        a = _scan(tree)
    except SyntaxError:
        # Can't statically analyze — report honestly rather than guessing.
        return {
            "timeComplexity": "unknown",
            "spaceComplexity": "unknown",
            "expectedComplexity": "unknown",
            "issue": "The source could not be parsed, so static analysis is unavailable.",
            "optimization": "Fix the syntax error, then re-run the analyzer.",
            "optimizedCode": code,
            "activeLineInfo": active_line,
            "contextSummary": _summary(snapshot, variables),
        }

    # Deep recursion observed at runtime strengthens a recursion verdict even
    # when the static scan is ambiguous.
    deep_stack = evidence["stack_depth"] >= 4

    time_c = "O(n)"
    space_c = "O(1)"
    expected = "O(n)"
    issue = "Linear execution path — no obvious complexity bottleneck detected."
    optimization = "Algorithm is operating within standard complexity bounds."

    if a.has_backtracking and (a.has_recursion or deep_stack):
        time_c = "O(bᵈ) — exponential search tree"
        space_c = "O(d) recursion stack"
        expected = "Sub-exponential with pruning"
        issue = (
            "Recursive search with state mutation and undo (backtracking) explores "
            "a large combinatorial state-tree."
        )
        optimization = (
            "Add constraint propagation / early pruning, memoize repeated subproblems, "
            "or reformulate as dynamic programming where subproblems overlap."
        )
    elif a.max_loop_depth >= 2:
        exp = a.max_loop_depth
        time_c = f"O(n^{exp})" if exp > 2 else "O(n²)"
        space_c = "O(1)"
        issue = (
            f"{exp}-level nested iteration detected. Inner loops repeatedly rescan the "
            "collection for every outer element."
        )
        optimization = (
            "Replace inner scans with a hash set / dict lookup, a two-pointer sweep, or "
            "precomputed prefix sums to drop a factor of n."
        )
        expected = "O(n) time, O(n) space"
    elif a.has_recursion:
        time_c = "O(n)"
        space_c = "O(n) recursion stack"
        if a.has_memoization:
            issue = "Recursion with memoization — repeated subproblems are already cached."
            optimization = "Looks good. Watch stack depth for very large inputs."
            expected = "O(n) time, O(n) space"
        else:
            issue = "Recursive formulation carries call-stack overhead and risks recomputation."
            optimization = (
                "Memoize overlapping subproblems, or convert to an iterative form with an "
                "explicit accumulator/stack if depth may be large."
            )
            expected = "O(n) time, O(1) space (iterative)"
    elif a.max_loop_depth == 1:
        time_c = "O(n)"
        space_c = "O(1)"
        issue = "Single linear pass over the input."
        optimization = "Already linear; focus optimization effort elsewhere."
        expected = "O(n)"

    return {
        "timeComplexity": time_c,
        "spaceComplexity": space_c,
        "expectedComplexity": expected,
        "issue": issue,
        "optimization": optimization,
        "optimizedCode": code,  # deterministic analyzer never rewrites code
        "activeLineInfo": active_line,
        "contextSummary": _summary(snapshot, variables),
    }


def _summary(snapshot: Optional[Dict[str, Any]], variables: Dict[str, Any]) -> str:
    step = (snapshot or {}).get("step", 0)
    fn = (snapshot or {}).get("function", "global")
    return f"Step {step} in {fn} with {len(variables)} active variable(s)."
