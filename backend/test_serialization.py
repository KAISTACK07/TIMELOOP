from app.engine.executor import ExecutionEngine

engine = ExecutionEngine()

def run_test(name, code, mode="smart"):
    print(f"=== {name} ===")
    res = engine.run(code, mode)
    snaps = res.get("snapshots", [])
    print("num snapshots:", len(snaps))
    print("error:", res.get("error"))
    print("truncated:", res.get("truncated"))
    print()

circular_code = '''
class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

a = Node(1)
b = Node(2)
a.next = b
b.next = a
'''

deep_recursion_code = '''
def deep_func(n):
    if n == 0:
        return 0
    return deep_func(n - 1) + 1

res = deep_func(500)
'''

if __name__ == '__main__':
    run_test("Circular Reference", circular_code, "smart")
    run_test("Deep Recursion", deep_recursion_code, "smart")
