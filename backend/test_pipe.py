import time
import threading
from multiprocessing import Process, Pipe
from app.engine.worker import worker_main

code = """
def solve_nqueens(n):
    def is_safe(board, row, col):
        for i in range(row):
            if board[i] == col or \
               board[i] - i == col - row or \
               board[i] + i == col + row:
                return False
        return True
    def solve(row, board):
        if row == n:
            return 1
        count = 0
        for col in range(n):
            if is_safe(board, row, col):
                board[row] = col
                count += solve(row + 1, board)
        return count
    return solve(0, [-1] * n)
solve_nqueens(6)
"""

def run_test():
    parent_conn, child_conn = Pipe()
    process = Process(target=worker_main, args=(code, child_conn, "smart"))
    
    t0 = time.time()
    process.start()
    
    # Read in a background thread to prevent deadlock
    res = []
    def reader():
        if parent_conn.poll(15):
            res.append(parent_conn.recv())
    
    t = threading.Thread(target=reader)
    t.start()
    
    process.join(10)
    
    if process.is_alive():
        print(f"Timeout! Worker is still alive after {time.time() - t0:.2f}s")
        process.terminate()
        process.join()
    else:
        t.join()
        if res:
            print(f"Success, snapshots: {len(res[0]['snapshots'])}")
        else:
            print("Worker exited but no data")

if __name__ == "__main__":
    run_test()
