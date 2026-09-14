import unittest

from app.engine.executor import ExecutionEngine


class Phase6RegressionTests(unittest.TestCase):
    def run_code(self, code, mode="smart"):
        return ExecutionEngine().run(code, mode)

    def test_smart_mode_records_handled_zero_division(self):
        code = """
def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return "division error"

result = divide(10, 0)
"""
        result = self.run_code(code, "smart")

        self.assertIsNone(result["error"])
        self.assertFalse(result["truncated"])
        self.assertEqual(
            result["snapshots"][-1].get("delta", {}).get("result"),
            "division error",
        )

        handled = [
            snap for snap in result["snapshots"]
            if snap["event"] == "exception_handled"
        ]
        self.assertEqual(len(handled), 1)
        self.assertEqual(handled[0]["function"], "divide")
        self.assertEqual(
            handled[0].get("value", {}).get("exception_type"),
            "ZeroDivisionError",
        )

    def test_smart_mode_records_selected_except_handler(self):
        code = """
def parse(value):
    try:
        return int(value)
    except TypeError:
        return "type"
    except ValueError:
        return "value"

result = parse("not-a-number")
"""
        result = self.run_code(code, "smart")

        self.assertIsNone(result["error"])
        self.assertEqual(result["snapshots"][-1].get("delta", {}).get("result"), "value")

        handled = [
            snap for snap in result["snapshots"]
            if snap["event"] == "exception_handled"
        ]
        self.assertEqual(len(handled), 1)
        self.assertEqual(handled[0].get("value", {}).get("exception_type"), "ValueError")

    def test_smart_mode_records_yield_points_for_list_consumption(self):
        code = """
def numbers():
    yield 1
    yield 2
    yield 3

result = list(numbers())
"""
        result = self.run_code(code, "smart")

        self.assertIsNone(result["error"])
        self.assertEqual(result["snapshots"][-1].get("delta", {}).get("result"), [1, 2, 3])

        yields = [snap for snap in result["snapshots"] if snap["event"] == "yield"]
        self.assertEqual([snap["value"] for snap in yields], [1, 2, 3])
        self.assertTrue(all(snap["function"] == "numbers" for snap in yields))
        self.assertEqual(result["snapshots"][-1]["function"], "global")

    def test_smart_mode_records_yield_points_for_next(self):
        code = """
def numbers():
    yield 1
    yield 2

it = numbers()
a = next(it)
b = next(it)
"""
        result = self.run_code(code, "smart")

        self.assertIsNone(result["error"])
        yields = [snap for snap in result["snapshots"] if snap["event"] == "yield"]
        self.assertEqual([snap["value"] for snap in yields], [1, 2])
        self.assertEqual(result["snapshots"][-1].get("delta", {}).get("b"), 2)
        self.assertEqual(result["snapshots"][-1]["function"], "global")


if __name__ == "__main__":
    unittest.main()
