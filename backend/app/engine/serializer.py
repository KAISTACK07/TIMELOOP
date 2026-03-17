from collections.abc import Iterable
import types
MAX_CONTAINER = 50
MAX_STRING = 200


def safe_serialize(value, depth=0, max_depth=3):
    if depth > max_depth:
        return "..."

    # Primitives
    if isinstance(value, (int, float, bool, type(None))):
        return value

    if isinstance(value, str):
        if len(value) > MAX_STRING:
            return value[:MAX_STRING] + "...(truncated)"
        return value

    # List / Tuple
    if isinstance(value, (list, tuple)):
        return [
            safe_serialize(v, depth + 1)
            for v in value[:MAX_CONTAINER]
        ]

    # Dict
    if isinstance(value, dict):
        items = list(value.items())[:MAX_CONTAINER]
        return {
            str(k): safe_serialize(v, depth + 1)
            for k, v in items
        }
    if isinstance(value, types.FunctionType):
        return f"<function {value.__name__}>"   
    # Fallback
    return str(value)