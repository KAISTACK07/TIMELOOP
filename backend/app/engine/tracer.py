import sys
from .serializer import safe_serialize

DEFAULT_MAX_STEPS = 20000
DEFAULT_MAX_DEPTH = 1000


class Tracer:
    def __init__(self, mode="fast", max_steps=DEFAULT_MAX_STEPS, max_depth=DEFAULT_MAX_DEPTH):
        self.mode = mode
        self.snapshots = []
        self.step = 0
        self.truncated = False
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.variable_history = {}
        self.prev_locals = {}
        self.checkpoint_interval = 50
        self.line_index = {}

    def _check_depth(self, frame):
        depth = 0
        f = frame
        while f:
            depth += 1
            if depth > self.max_depth:
                self.truncated = True
                raise StopIteration("Max call depth exceeded")
            f = f.f_back

    def compute_delta(self, prev, curr):
        delta = {}

        for key in curr:
            if key not in prev or prev[key] != curr[key]:
                delta[key] = curr[key]

        for key in prev:
            if key not in curr:
                delta[key] = "__deleted__"

        return delta

    def trace(self, frame, event, arg):

        self._check_depth(frame)
        

        # --- Dual mode event filtering ---

        # Convert module return into line   event
        # HARD LIMIT for FAST mode
        if self.mode == "fast":
            if self.step > 2000:
                self.truncated = True
                raise StopIteration("Fast mode step limit reached")
        if event == "return" and frame.f_code.co_name == "<module>":
            event = "line"

        if self.mode == "fast":
            if event == "call":
                if frame.f_code.co_filename != "<string>":
                    return self.trace

            elif event == "line":
                # allow only global scope
                if frame.f_code.co_name != "<module>":
                    return self.trace

            elif event != "exception":
                return self.trace

        else:  # detailed mode
            if event not in ("line", "call", "return", "exception"):
                return self.trace 
        
        self.step += 1

        function_name = frame.f_code.co_name
        if function_name == "<module>":
            function_name = "global"
        
        #  Serialize locals
        locals_dict = {}
        for k, v in dict(frame.f_locals).items():
            if k == "__builtins__":
                continue
            if k in ("globals", "locals", "fromlist", "level", "ALLOWED_MODULES"):
                continue
            if k.startswith("__"):
                continue
            # skip heavy objects
            if isinstance(v, (int, float, str, bool)):
                locals_dict[k] = v
            else:
                locals_dict[k] = str(type(v).__name__)
        
        curr = locals_dict.copy()
        
        # skip if no meaningful change (FAST mode only)
        if self.mode == "fast" and event == "line":
            delta = self.compute_delta(self.prev_locals, curr)
            if not delta:
                return self.trace
            
        

        # Skip useless first empty snapshot
        if not self.snapshots and not curr:
            self.step -= 1
            return self.trace

        #  Build call stack
        stack = []
        f = frame
        while f:
            if "<string>" in f.f_code.co_filename:
                name = f.f_code.co_name
                if name == "<module>":
                    name = "global"
                stack.append(name)
            f = f.f_back

        stack.reverse()

        clean_stack = []
        for name in stack:
            if not clean_stack or clean_stack[-1] != name:
                clean_stack.append(name)

        stack = clean_stack
        
        snapshot = {
            "step": self.step,
            "event": event,
            "line_no": frame.f_lineno,
            "function": function_name,
            "stack": stack
        }

        #  First snapshot
        if not self.snapshots or self.step % self.checkpoint_interval == 0:
            snapshot["locals"] = curr
            snapshot["is_full"] = True

        else:
            delta = self.compute_delta(self.prev_locals, curr)

            # DO NOT skip if exception
            if not delta and event not in ("exception", "return"):
                return self.trace

            snapshot["delta"] = delta
            snapshot["is_full"] = False

        #  Exception handling
        if event == "exception":
            exc_type, exc_value, exc_traceback = arg
            if snapshot["is_full"]:
                snapshot["locals"]["error"] = str(exc_value)
            else:
                snapshot["delta"]["error"] = str(exc_value)
        # Skip duplicate line events with same state
        if self.snapshots:
            last = self.snapshots[-1]

            if (
                last["line_no"] == snapshot["line_no"]
                and last["function"] == snapshot["function"]
                and last.get("delta") == snapshot.get("delta")
            ):
                return self.trace
        self.snapshots.append(snapshot)
        line_no = snapshot["line_no"]

        if line_no not in self.line_index:
            self.line_index[line_no] = []

        self.line_index[line_no].append(snapshot["step"])   
        current_index = len(self.snapshots) - 1

        #  Variable history (ONLY GLOBAL SCOPE)
        if function_name == "global":

            if snapshot["is_full"]:
                items = curr.items()
            else:
                items = snapshot["delta"].items()

            for name, value in items:
                if value == "__deleted__":
                    continue

                history = self.variable_history.setdefault(name, [])
                if not history or history[-1][1] != value:
                   history.append((self.step, value))

        #  Update state
        self.prev_locals = curr.copy()

        #  Safety
        if self.step >= self.max_steps:
            self.truncated = True
            raise StopIteration("Max steps exceeded")

        return self.trace