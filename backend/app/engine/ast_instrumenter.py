import ast

from .ast.expression_transformer import ExpressionTransformerMixin
from .ast.control_flow_transformer import ControlFlowTransformerMixin


# ── Helpers ──────────────────────────────────────────────────

def _code_has_semantic_events(tree: ast.AST) -> bool:
    """Check if the code contains any __semantic_event__() calls."""
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Name) and
                node.func.id == "__semantic_event__"):
            return True
    return False


def _make_semantic_call(event_name: str, data_dict: ast.AST, lineno: int, func_name: str = "global") -> ast.Expr:
    """Build AST for: __semantic_event__(event_name, data_dict, __line__=lineno, __func__=func_name)"""
    call = ast.Call(
        func=ast.Name(id="__semantic_event__", ctx=ast.Load()),
        args=[ast.Constant(value=event_name), data_dict],
        keywords=[
            ast.keyword(arg="__line__", value=ast.Constant(value=lineno)),
            ast.keyword(arg="__func__", value=ast.Constant(value=func_name))
        ]
    )
    stmt = ast.Expr(value=call)
    stmt.lineno = lineno
    stmt.col_offset = 0
    call.lineno = lineno
    call.col_offset = 0
    return stmt


# ── Full Instrumenter (smart / detailed mode) ────────────────

class Instrumenter(
    ExpressionTransformerMixin,
    ControlFlowTransformerMixin,
    ast.NodeTransformer
):
    pass


# ── Reduced-mode Instrumenter ────────────────────────────────

class ReducedInstrumenter(ast.NodeTransformer):
    """Reduced-mode AST transformer.

    Leaves ALL function bodies untouched for native execution speed.
    __semantic_event__() calls inside functions are already plain
    Python calls (they start with "__" so expression_transformer
    skips them) — they fire naturally without AST rewriting.

    We traverse the AST only to find explicit __semantic_event__ calls
    and inject static __line__ and __func__ metadata into them. This
    prevents expensive sys._getframe() calls at runtime.

    FALLBACK: If the code has NO explicit __semantic_event__() calls,
    injects sparse auto-checkpoints into top-level FunctionDefs:
      - function_entry (with argument values)
      - function_complete (in finally block, guaranteed to fire)

    These provide minimal timeline visibility for algorithms that
    don't have user-authored semantic events.
    """

    def __init__(self, needs_fallback: bool = False):
        super().__init__()
        self._needs_fallback = needs_fallback
        self._current_function = "global"

    def visit_FunctionDef(self, node):
        is_top_level = (self._current_function == "global")
        
        prev_func = self._current_function
        self._current_function = node.name

        # Recurse to find __semantic_event__ calls inside the body
        self.generic_visit(node)

        if self._needs_fallback and is_top_level:
            # Inject sparse auto-checkpoints for top-level functions.
            # Build data dict: {"name": "dfs", "args": {"graph": graph, ...}}
            arg_names = [a.arg for a in node.args.args]
            args_dict = ast.Dict(
                keys=[ast.Constant(value=n) for n in arg_names],
                values=[ast.Name(id=n, ctx=ast.Load()) for n in arg_names]
            )
            entry_data = ast.Dict(
                keys=[ast.Constant(value="name"), ast.Constant(value="args")],
                values=[ast.Constant(value=node.name), args_dict]
            )
            complete_data = ast.Dict(
                keys=[ast.Constant(value="name")],
                values=[ast.Constant(value=node.name)]
            )

            entry = _make_semantic_call("function_entry", entry_data, node.lineno, node.name)
            complete = _make_semantic_call("function_complete", complete_data, node.lineno, node.name)

            # Wrap body in try/finally so completion fires even on early return
            try_node = ast.Try(
                body=node.body,
                handlers=[],
                orelse=[],
                finalbody=[complete]
            )
            try_node.lineno = node.lineno
            try_node.col_offset = 0

            node.body = [entry, try_node]

        self._current_function = prev_func
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "__semantic_event__":
            # Inject static metadata kwargs to avoid runtime frame introspection
            has_line = any(k.arg == "__line__" for k in node.keywords)
            if not has_line:
                node.keywords.append(ast.keyword(arg="__line__", value=ast.Constant(value=node.lineno)))
            has_func = any(k.arg == "__func__" for k in node.keywords)
            if not has_func:
                node.keywords.append(ast.keyword(arg="__func__", value=ast.Constant(value=self._current_function)))
        return node


# ── Public API ───────────────────────────────────────────────

def instrument_code(code_str: str, mode: str = "smart"):
    """
    Parses the user code, transforms it using the appropriate
    Instrumenter, and returns a compiled code object.

    In reduced mode, NO function bodies are instrumented.
    If the code lacks __semantic_event__() calls, sparse auto-
    checkpoints are injected into top-level functions.
    """
    tree = ast.parse(code_str)

    if mode == "reduced":
        needs_fallback = not _code_has_semantic_events(tree)
        instrumenter = ReducedInstrumenter(needs_fallback=needs_fallback)
    else:
        instrumenter = Instrumenter()

    instrumented_tree = instrumenter.visit(tree)
    ast.fix_missing_locations(instrumented_tree)
    return compile(instrumented_tree, filename="<sandbox>", mode="exec")