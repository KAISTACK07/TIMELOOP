from app.engine.executor import ExecutionEngine

code = """
def process():
    data = [1, 2, 3]
    try:
        data.append(4)
        run_inner(data)
    except Exception as e:
        data.append(5)
    return data

def run_inner(d):
    d.pop()
    raise ValueError("Test Error")

res = process()
"""

def test():
    engine = ExecutionEngine()
    result = engine.run(code, mode="smart")
    
    if result.get("error"):
        print("❌ Error:", result["error"])
        return

    snapshots = result.get("snapshots", [])
    print(f"Total steps: {len(snapshots)}")
    
    for s in snapshots:
        val = s.get("value")
        evt = s.get("event")
        delta = s.get("delta")
        print(f"step={s['step']} evt={evt} func={s.get('function')} line={s.get('line_no')} delta={delta} val={val}")

if __name__ == "__main__":
    test()
