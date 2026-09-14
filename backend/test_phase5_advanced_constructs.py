from app.engine.executor import ExecutionEngine


def _run(code: str):
    return ExecutionEngine().run(code, mode="smart")


def test_generator_resume_is_deterministic_but_not_return_closed():
    code = """
def gen(n):
    i = 0
    while i < n:
        yield i
        i += 1

g = gen(2)
a = next(g)
b = next(g)
"""
    result = _run(code)
    assert result["error"] is None
    events = [s["event"] for s in result["snapshots"]]
    assert "call" in events
    # No synthetic generator-complete return should be assumed here.
    assert not any(s["event"] == "return" and s.get("function") == "gen" for s in result["snapshots"])


def test_async_direct_step_executes_without_event_loop_guarantee():
    code = """
async def f(x):
    return x + 1

async def main():
    v = await f(2)
    return v

coro = main()
try:
    coro.send(None)
except StopIteration as e:
    out = e.value
"""
    result = _run(code)
    assert result["error"] is None
    # Direct coroutine stepping should remain deterministic.
    assert any(s["event"] == "return" and s.get("function") == "main" for s in result["snapshots"])


def test_decorator_wrapper_identity_is_visible_but_ambiguous():
    code = """
def dec(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

@dec
def add(x, y):
    return x + y

z = add(4,5)
"""
    result = _run(code)
    assert result["error"] is None
    calls = [c["name"] for c in result.get("function_calls", [])]
    assert "add" in calls
    # Wrapped target can surface as closure/local identity.
    assert "fn" in calls


def test_closure_nonlocal_mutation_is_visible():
    code = """
def outer():
    x = 0
    def inner():
        nonlocal x
        x += 1
        return x
    a = inner()
    b = inner()
    return a, b, x

res = outer()
"""
    result = _run(code)
    assert result["error"] is None
    # Closure-cell ownership is not guaranteed in variable_history, but inner
    # increments should still be replay-visible as line deltas.
    inner_x_deltas = [
        s.get("delta", {}).get("x")
        for s in result["snapshots"]
        if s["event"] == "line" and s.get("function") == "inner"
    ]
    assert 1 in inner_x_deltas and 2 in inner_x_deltas


def test_lambda_executes_as_regular_callable():
    code = """
inc = lambda x: x + 1
res = inc(2)
"""
    result = _run(code)
    assert result["error"] is None
    assert any(c["name"] == "inc" for c in result.get("function_calls", []))


def test_comprehensions_are_atomic_at_statement_level():
    code = """
a = [i*i for i in range(4)]
b = {i:i*i for i in range(3)}
"""
    result = _run(code)
    assert result["error"] is None
    line_events = [s for s in result["snapshots"] if s["event"] == "line"]
    # One assignment event per statement-level assignment.
    assert len(line_events) == 2


def test_context_manager_order_executes_without_full_dunder_ownership():
    code = """
class C:
    def __enter__(self):
        return 10
    def __exit__(self, exc_type, exc, tb):
        return False

with C() as v:
    x = v + 1
"""
    result = _run(code)
    assert result["error"] is None
    # __enter__ result is visible through return value.
    assert any(
        s["event"] == "return" and s.get("value") == 10
        for s in result["snapshots"]
    )
