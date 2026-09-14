import ast
from .base_transformer import BaseInstrumenterMixin

class ControlFlowTransformerMixin(BaseInstrumenterMixin):
    # --- If ---
    def visit_If(self, node):
        branches = []
        curr = node
        branch_idx = 0
        while isinstance(curr, ast.If):
            curr_test = self.visit(curr.test)
            
            curr_body = []
            for stmt in curr.body:
                res = self.visit(stmt)
                if isinstance(res, list):
                    curr_body.extend(res)
                elif res is not None:
                    curr_body.append(res)
            
            branch_name = "then" if branch_idx == 0 else "elif"
            branches.append((curr_test, curr_body, curr.lineno, branch_name))
            
            branch_idx += 1
            if len(curr.orelse) == 1 and isinstance(curr.orelse[0], ast.If):
                curr = curr.orelse[0]
            else:
                else_body = []
                for stmt in curr.orelse:
                    res = self.visit(stmt)
                    if isinstance(res, list):
                        else_body.extend(res)
                    elif res is not None:
                        else_body.append(res)
                break
                
        expr = ast.Tuple(elts=[ast.Constant(value="else"), ast.Constant(value=node.lineno), ast.Constant(value=-1)], ctx=ast.Load())
        
        for route_idx, (test, body, lineno, branch_name) in reversed(list(enumerate(branches))):
            expr = ast.IfExp(
                test=test,
                body=ast.Tuple(elts=[ast.Constant(value=branch_name), ast.Constant(value=lineno), ast.Constant(value=route_idx)], ctx=ast.Load()),
                orelse=expr
            )
            
        tmp_name = f"__branch_{node.lineno}_{id(node)}__"
        
        assign_tmp = ast.Assign(
            targets=[ast.Tuple(elts=[
                ast.Name(id=f"{tmp_name}_name", ctx=ast.Store()),
                ast.Name(id=f"{tmp_name}_line", ctx=ast.Store()),
                ast.Name(id=f"{tmp_name}_route", ctx=ast.Store())
            ], ctx=ast.Store())],
            value=expr
        )
        ast.copy_location(assign_tmp, node)
        
        log_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="__log_if_chain__", ctx=ast.Load()),
                args=[
                    ast.Name(id=f"{tmp_name}_name", ctx=ast.Load()),
                    ast.Name(id=f"{tmp_name}_line", ctx=ast.Load()),
                    ast.Constant(value=node.lineno)
                ],
                keywords=[]
            )
        )
        ast.copy_location(log_call, node)
        
        reconstructed_orelse = else_body
        for route_idx, (test, body, lineno, branch_name) in reversed(list(enumerate(branches))):
            cmp_test = ast.Compare(
                left=ast.Name(id=f"{tmp_name}_route", ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=route_idx)]
            )
            curr_if = ast.If(
                test=cmp_test,
                body=body,
                orelse=reconstructed_orelse
            )
            ast.copy_location(curr_if, node)
            reconstructed_orelse = [curr_if]
            
        return [assign_tmp, log_call, curr_if]

    # --- For Loop ---
    def visit_For(self, node):
        node = self.generic_visit(node)
        
        # Extract target variable names for loop_var tracking
        targets = [n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)]
        target_names_node = ast.List(
            elts=[ast.Constant(value=t) for t in targets],
            ctx=ast.Load()
        )
        
        new_iter = ast.Call(
            func=ast.Name(id="__for__", ctx=ast.Load()),
            args=[node.iter, ast.Constant(value=node.lineno), target_names_node],
            keywords=[]
        )
        ast.copy_location(new_iter, node.iter)
        
        for_node = ast.For(
            target=node.target,
            iter=new_iter,
            body=node.body,
            orelse=node.orelse
        )
        ast.copy_location(for_node, node)
        
        enter_call = ast.Expr(
            value=ast.Call(func=ast.Name(id="__loop_enter__", ctx=ast.Load()), args=[], keywords=[])
        )
        ast.copy_location(enter_call, node)
        
        exit_call = ast.Expr(
            value=ast.Call(func=ast.Name(id="__loop_exit__", ctx=ast.Load()), args=[], keywords=[])
        )
        ast.copy_location(exit_call, node)
        
        try_node = ast.Try(
            body=[for_node],
            handlers=[],
            orelse=[],
            finalbody=[exit_call]
        )
        ast.copy_location(try_node, node)
        
        return [enter_call, try_node]

    # --- While Loop ---
    def visit_While(self, node):
        node = self.generic_visit(node)
        
        new_test = ast.Call(
            func=ast.Name(id="__while_cond__", ctx=ast.Load()),
            args=[node.test, ast.Constant(value=node.lineno)],
            keywords=[]
        )
        ast.copy_location(new_test, node.test)
        
        while_node = ast.While(
            test=new_test,
            body=node.body,
            orelse=node.orelse
        )
        ast.copy_location(while_node, node)
        
        enter_call = ast.Expr(
            value=ast.Call(func=ast.Name(id="__loop_enter__", ctx=ast.Load()), args=[], keywords=[])
        )
        ast.copy_location(enter_call, node)
        
        exit_call = ast.Expr(
            value=ast.Call(func=ast.Name(id="__loop_exit__", ctx=ast.Load()), args=[], keywords=[])
        )
        ast.copy_location(exit_call, node)
        
        try_node = ast.Try(
            body=[while_node],
            handlers=[],
            orelse=[],
            finalbody=[exit_call]
        )
        ast.copy_location(try_node, node)
        
        return [enter_call, try_node]

    # --- Break / Continue ---
    def visit_Break(self, node):
        log_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="__break__", ctx=ast.Load()),
                args=[ast.Constant(value=node.lineno)],
                keywords=[]
            )
        )
        ast.copy_location(log_call, node)
        return [log_call, node]

    def visit_Continue(self, node):
        log_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="__continue__", ctx=ast.Load()),
                args=[ast.Constant(value=node.lineno)],
                keywords=[]
            )
        )
        ast.copy_location(log_call, node)
        return [log_call, node]

    # --- Try / Except ---
    def visit_Try(self, node):
        node.body = self._visit_stmt_list(node.body)
        node.orelse = self._visit_stmt_list(node.orelse)
        node.finalbody = self._visit_stmt_list(node.finalbody)

        for handler in node.handlers:
            handler.body = self._visit_stmt_list(handler.body)
            handler_type = self._exception_type_label(handler.type)
            log_call = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="__exception_handled__", ctx=ast.Load()),
                    args=[
                        ast.Constant(value=handler_type),
                        ast.Constant(value=handler.lineno),
                    ],
                    keywords=[]
                )
            )
            ast.copy_location(log_call, handler)
            handler.body.insert(0, log_call)

        return node

    def _visit_stmt_list(self, statements):
        visited = []
        for stmt in statements:
            res = self.visit(stmt)
            if isinstance(res, list):
                visited.extend(res)
            elif res is not None:
                visited.append(res)
        return visited

    def _exception_type_label(self, node):
        if node is None:
            return "BaseException"
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            curr = node
            while isinstance(curr, ast.Attribute):
                parts.append(curr.attr)
                curr = curr.value
            if isinstance(curr, ast.Name):
                parts.append(curr.id)
            return ".".join(reversed(parts))
        if isinstance(node, ast.Tuple):
            return ", ".join(self._exception_type_label(elt) for elt in node.elts)
        return type(node).__name__
