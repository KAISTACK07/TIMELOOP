import sys
from .serializer import safe_serialize

DEFAULT_MAX_STEPS = 5000
DEFAULT_MAX_DEPTH = 1000


class Tracer:
    def __init__(self, max_steps=DEFAULT_MAX_STEPS, max_depth=DEFAULT_MAX_DEPTH):
        self.snapshots = []
        self.step = 0
        self.truncated = False
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.variable_history = {}

    def _check_depth(self, frame):
        depth = 0
        f = frame
        while f:
            depth += 1
            if depth > self.max_depth:
                self.truncated = True
                raise StopIteration("Max call depth exceeded")
            f = f.f_back

    def trace(self, frame, event, arg):

        # Enforce call depth protection
        self._check_depth(frame)

        # Increment step ONLY for executable lines
        if event == "line":
            self.step += 1

        # Normalize function name
        function_name = frame.f_code.co_name
        if function_name == "<module>":
            function_name = "global"

        # Build snapshot safely
        locals_dict = {}

        for k, v in dict(frame.f_locals).items():
            if k == "__builtins__":
                continue

            value = safe_serialize(v)
            locals_dict[k] = value

            # record variable history
            history = self.variable_history.setdefault(k, [])

            if not history or history[-1][1] != value:
                history.append((len(self.snapshots), value))

        snapshot = {
            "step": self.step,
            "event": event,
            "line_no": frame.f_lineno,
            "function": function_name,
            "locals": locals_dict,
        }

        # Exception handling
        if event == "exception":
            exc_type, exc_value, exc_traceback = arg
            snapshot["locals"]["error"] = str(exc_value)

        # Store snapshot BEFORE enforcing step limit
        self.snapshots.append(snapshot)

        # Enforce max step protection
        if self.step >= self.max_steps:
            self.truncated = True
            raise StopIteration("Max steps exceeded")

        return self.trace