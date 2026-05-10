import ast
import uuid
from .base_transformer import BaseInstrumenterMixin

class ExpressionTransformerMixin(BaseInstrumenterMixin):
    # --- Assign ---
    def visit_Assign(self, node):
        node = self.generic_visit(node)
        stmts = [node]
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            log_call = self._make_var_log(var_name, node.lineno)
            ast.copy_location(log_call, node)
            stmts.append(log_call)
        return stmts

    def visit_AugAssign(self, node):
        node = self.generic_visit(node)
        stmts = [node]
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            log_call = self._make_var_log(var_name, node.lineno)
            ast.copy_location(log_call, node)
            stmts.append(log_call)
        return stmts

    def visit_AnnAssign(self, node):
        node = self.generic_visit(node)
        stmts = [node]
        if node.value is not None and isinstance(node.target, ast.Name):
            var_name = node.target.id
            log_call = self._make_var_log(var_name, node.lineno)
            ast.copy_location(log_call, node)
            stmts.append(log_call)
        return stmts

    # --- Call ---
    def visit_Call(self, node):
        node = self.generic_visit(node)

        # Extract a reasonable name for the function logging
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name.startswith("__"):
                return node
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        else:
            func_name = "<callable>"

        func_name_node = ast.Constant(value=func_name)
        line_no_node = ast.Constant(value=node.lineno)

        new_call = ast.Call(
            func=ast.Name(id="__call__", ctx=ast.Load()),
            args=[func_name_node, line_no_node, node.func] + node.args,
            keywords=node.keywords
        )
        ast.copy_location(new_call, node)
        return new_call

    # --- Expr (statement-level method calls → mutation tracking) ---
    def visit_Expr(self, node):
        # Detect: var.method(...) as a standalone statement (e.g., res.append(i))
        # Must detect BEFORE generic_visit transforms the inner Call node.
        is_method_call = (isinstance(node.value, ast.Call) and
                          isinstance(node.value.func, ast.Attribute) and
                          isinstance(node.value.func.value, ast.Name))
        
        var_name = node.value.func.value.id if is_method_call else None

        node = self.generic_visit(node)

        if is_method_call and var_name and not var_name.startswith("__"):
            # Inject __log__ AFTER the method call to capture mutation
            log_call = self._make_var_log(var_name, node.lineno)
            ast.copy_location(log_call, node)
            return [node, log_call]

        return node

    # --- Return ---
    def visit_Return(self, node):
        node = self.generic_visit(node)
        if node.value is None:
            return node
            
        tmp_name = f"__tmp_ret_{uuid.uuid4().hex[:8]}__"
        
        assign_tmp = ast.Assign(
            targets=[ast.Name(id=tmp_name, ctx=ast.Store())],
            value=node.value
        )
        ast.copy_location(assign_tmp, node)
        
        return_log = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="__return__", ctx=ast.Load()),
                args=[
                    ast.Constant(value="__current__"),
                    ast.Name(id=tmp_name, ctx=ast.Load()),
                    ast.Constant(value=node.lineno)
                ],
                keywords=[]
            )
        )
        ast.copy_location(return_log, node)
        
        new_return = ast.Return(value=ast.Name(id=tmp_name, ctx=ast.Load()))
        ast.copy_location(new_return, node)
        
        return [assign_tmp, return_log, new_return]
