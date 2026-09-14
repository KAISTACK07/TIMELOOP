import time
from app.engine.executor import ExecutionEngine

engine = ExecutionEngine()

nqueens_code = '''
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
result = solve_nqueens({})
'''

if __name__ == '__main__':
    for n in [4, 5, 6, 7, 8]:
        code = nqueens_code.format(n)
        start_time = time.time()
        res = engine.run(code, mode="smart")
        end_time = time.time()
        runtime = end_time - start_time
        
        snaps = res.get("snapshots", [])
        truncated = res.get("truncated", False)
        error = res.get("error", None)
        
        print(f"--- N={n} ---")
        print(f"Runtime (s): {runtime:.4f}")
        print(f"Snapshots: {len(snaps)}")
        print(f"Truncated: {truncated}")
        print(f"Error: {error}")
        
        solution = None
        var_hist = res.get("variable_history", {})
        if "result" in var_hist:
            hist = var_hist["result"]
            if hist:
                solution = hist[-1][1]
        print(f"Solution: {solution}")
        print()
