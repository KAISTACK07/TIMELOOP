from app.engine.executor import ExecutionEngine
from collections import Counter

code_nqueens = """
def n_queens(n):
    board = []
    
    def solve(row):
        if row == n:
            __semantic_event__("solution_found", {"board": list(board)})
            return True
            
        for col in range(n):
            if is_safe(row, col):
                board.append((row, col))
                __semantic_event__("queen_placed", {"row": row, "col": col})
                solve(row + 1)
                board.pop()
                __semantic_event__("queen_removed", {"row": row, "col": col})
                
    def is_safe(row, col):
        for r, c in board:
            if c == col or abs(r - row) == abs(c - col):
                return False
        return True
        
    solve(0)
    return board

n_queens(4)
"""

code_sudoku = """
def solve_sudoku(board):
    def find_empty():
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return (i, j)
        return None

    def is_valid(num, pos):
        row, col = pos
        for j in range(9):
            if board[row][j] == num and j != col:
                return False
        for i in range(9):
            if board[i][col] == num and i != row:
                return False
        box_r, box_c = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_r, box_r + 3):
            for j in range(box_c, box_c + 3):
                if board[i][j] == num and (i, j) != pos:
                    return False
        return True

    def solve():
        empty = find_empty()
        if not empty:
            __semantic_event__("solved", {"status": "complete"})
            return True
        row, col = empty
        
        if col == 0 and row > 0:
            __semantic_event__("row_started", {"row": row})
            
        candidates_tried = 0
        for num in range(1, 10):
            if is_valid(num, (row, col)):
                board[row][col] = num
                candidates_tried += 1
                if solve():
                    return True
                board[row][col] = 0
                
        if candidates_tried > 0:
            __semantic_event__("branch_exhausted", {"row": row, "col": col, "candidates": candidates_tried})
            
        return False

    __semantic_event__("search_started", {})
    solve()
    return board

puzzle = [
    [5,3,0,0,7,0,0,0,0],
    [6,0,0,1,9,5,0,0,0],
    [0,9,8,0,0,0,0,6,0],
    [8,0,0,0,6,0,0,0,3],
    [4,0,0,8,0,3,0,0,1],
    [7,0,0,0,2,0,0,0,6],
    [0,6,0,0,0,0,2,8,0],
    [0,0,0,4,1,9,0,0,5],
    [0,0,0,0,8,0,0,7,9]
]
solve_sudoku(puzzle)
"""

# DFS WITHOUT semantic events — tests fallback auto-checkpoints
code_dfs_plain = """
def dfs(graph, start):
    visited = set()
    result = []
    
    def explore(node):
        if node in visited:
            return
        visited.add(node)
        result.append(node)
        for neighbor in sorted(graph.get(node, [])):
            explore(neighbor)
    
    explore(start)
    return result

graph = {
    'A': ['B', 'C'],
    'B': ['D', 'E'],
    'C': ['F'],
    'D': [],
    'E': ['F'],
    'F': []
}
dfs(graph, 'A')
"""


def run_test(name, code, mode):
    engine = ExecutionEngine()
    print(f"\n{'='*55}")
    print(f"  {name} — {mode.upper()} MODE")
    print(f"{'='*55}")

    res = engine.run(code, mode=mode)
    if res.get("error"):
        print(f"  ❌ Error: {res['error']}")
        return False

    snapshots = res.get("snapshots", [])
    print(f"  Total emitted steps: {len(snapshots)}")

    event_counts = Counter(s['event'] for s in snapshots)
    print(f"  Event breakdown:")
    for k, v in event_counts.items():
        print(f"    {k}: {v}")

    # Compression summary
    compression = res.get("compression")
    if compression:
        print(f"\n  📊 Compression summary:")
        print(f"    Total seen:    {compression['total_seen']}")
        print(f"    Total emitted: {compression['total_emitted']}")
        print(f"    Suppressed:    {compression['suppressed']}")
    else:
        print(f"  (no compression needed)")

    if mode == "reduced" and snapshots:
        funcs = set(s.get("function", "?") for s in snapshots)
        print(f"  Function ownership: {funcs}")

        print(f"\n  First 5 events:")
        for s in snapshots[:5]:
            val = s.get('value', '')
            print(f"    step={s['step']} line={s.get('line_no')} "
                  f"func={s.get('function')} value={val}")
        if len(snapshots) > 5:
            print(f"    ... ({len(snapshots) - 5} more)")
            print(f"  Last event:")
            s = snapshots[-1]
            print(f"    step={s['step']} line={s.get('line_no')} "
                  f"func={s.get('function')} value={s.get('value')}")

    return True


if __name__ == '__main__':
    # Test 1: N-Queens (semantic, moderate density)
    run_test("N-Queens", code_nqueens, "reduced")

    # Test 2: DFS plain (fallback checkpoints, no semantic events)
    run_test("DFS (plain — fallback)", code_dfs_plain, "reduced")

    # Test 3: Sudoku (high semantic density — compression test)
    run_test("Sudoku", code_sudoku, "reduced")
