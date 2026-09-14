from app.engine.executor import ExecutionEngine

engine = ExecutionEngine()

def run_test(name, code, mode="smart"):
    print(f"=== {name} ===")
    res = engine.run(code, mode)
    print("stdout:", repr(res.get("stdout")))
    print("error:", res.get("error"))
    print("truncated:", res.get("truncated"))
    print("num snapshots:", len(res.get("snapshots", [])))
    print()

counter_code = '''
class Counter:
    def __init__(self, n):
        self.n = n
        self.total = 0

    def increment(self):
        self.total += self.n
        return self.total

c = Counter(5)
a = c.increment()
b = c.increment()
print(a, b)
'''

nqueens = '''
def solve_nqueens(n):
    def is_safe(board, row, col):
        for i in range(row):
            if board[i] == col or board[i] - i == col - row or board[i] + i == col + row:
                return False
        return True
    def solve(row, board):
        if row == n: return 1
        count = 0
        for col in range(n):
            if is_safe(board, row, col):
                board[row] = col
                count += solve(row + 1, board)
        return count
    return solve(0, [-1] * n)
solve_nqueens({})
'''

if __name__ == '__main__':
    run_test("TEST 1", 'print("hello")\nprint(10 + 20)')
    run_test("TEST 2", 'print("before")\nraise RuntimeError("user error")')
    run_test("TEST 3", 'x = 10\nprint(x)')
    run_test("TEST 4", 'x = 10\ny = 20')
    run_test("TEST 5 Counter Detailed", counter_code, "detailed")
    run_test("TEST 5 Counter Smart", counter_code, "smart")
    run_test("TEST 5 Counter Reduced", counter_code, "reduced")
    run_test("TEST 6 N-Queens 4 Smart", nqueens.format(4), "smart")
    run_test("TEST 6 N-Queens 6 Smart", nqueens.format(6), "smart")
    run_test("TEST 6 N-Queens 8 Smart", nqueens.format(8), "smart")
