import urllib.request
import json
import sys

url = "http://127.0.0.1:8000/execute"
# The test case specified:
# def test_func():
#     n = 2
#     while n > 0:
#         n -= 1
# test_func()

data = json.dumps({
    "code": "def test_func():\n    n = 2\n    while n > 0:\n        n -= 1\n\ntest_func()",
    "mode": "smart"
}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        
        snapshots = result.get("snapshots", [])
        
        # Validation 1: call event line_no vs call_site_line
        call_events = [s for s in snapshots if s["event"] == "call"]
        if not call_events:
            print("❌ No call events found!")
            sys.exit(1)
            
        call_event = call_events[0]
        # function defined on line 1, called on line 6
        assert call_event["line_no"] == 1, f"Expected line_no=1, got {call_event['line_no']}"
        assert call_event["call_site_line"] == 6, f"Expected call_site_line=6, got {call_event['call_site_line']}"
        print("✅ Validation 1 Passed: call event line_no points to function definition, call_site_line points to invocation.")

        # Validation 2: Natural while termination emits value=false event
        while_events = [s for s in snapshots if s["event"] == "while"]
        
        if not while_events:
            print("❌ No while events found!")
            sys.exit(1)
            
        final_while = while_events[-1]
        assert final_while["value"] is False, "Final while event should have value=False"
        assert final_while["iteration"] == 2, "Final while event should be at iteration 2"
        print("✅ Validation 2 Passed: Natural while termination emits value=false event.")
        
        print("\nAll validations passed successfully!")

except Exception as e:
    print("Error during execution:", e)
    sys.exit(1)
