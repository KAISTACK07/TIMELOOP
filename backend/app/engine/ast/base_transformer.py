import ast

class BaseInstrumenterMixin:
    def _make_var_log(self, var_name: str, lineno: int) -> ast.Expr:
        return ast.Expr(
            value=ast.Call(
                func=ast.Name(id="__log__", ctx=ast.Load()),
                args=[
                    ast.Constant(value=var_name),
                    ast.Name(id=var_name, ctx=ast.Load()),
                    ast.Constant(value=lineno)
                ],
                keywords=[]
            )
        )
