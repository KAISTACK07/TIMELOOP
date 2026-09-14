import types

MAX_CONTAINER = 50
MAX_STRING = 200


def safe_serialize(value, depth=0, max_depth=4, _seen=None):
    if _seen is None:
        _seen = set()

    if depth > max_depth:
        return "..."

    # Primitives
    if isinstance(value, (int, float, bool, type(None))):
        return value

    if isinstance(value, str):
        if len(value) > MAX_STRING:
            return value[:MAX_STRING] + "...(truncated)"
        return value

    obj_id = id(value)
    if obj_id in _seen:
        return "<circular>"

    # List / Tuple
    if isinstance(value, (list, tuple)):
        _seen.add(obj_id)
        return [
            safe_serialize(v, depth + 1, max_depth, _seen)
            for v in value[:MAX_CONTAINER]
        ]

    if isinstance(value, set):
        _seen.add(obj_id)
        return [
            safe_serialize(v, depth + 1, max_depth, _seen)
            for v in sorted(list(value)[:MAX_CONTAINER], key=repr)
        ]

    # Dict
    if isinstance(value, dict):
        _seen.add(obj_id)
        items = list(value.items())[:MAX_CONTAINER]
        return {
            str(k): safe_serialize(v, depth + 1, max_depth, _seen)
            for k, v in items
        }

    if isinstance(value, types.FunctionType):
        return f"<function {value.__name__}>"
    if isinstance(value, types.MethodType):
        return f"<method {value.__name__}>"

    if hasattr(value, "__dict__"):
        _seen.add(obj_id)
        attrs = {}
        for key, attr_value in list(vars(value).items())[:MAX_CONTAINER]:
            if str(key).startswith("__"):
                continue
            attrs[str(key)] = safe_serialize(attr_value, depth + 1, max_depth, _seen)
        return {
            "__class__": value.__class__.__name__,
            "attributes": attrs,
        }

    # Fallback
    return str(value)
