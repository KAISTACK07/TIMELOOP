SAFE_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
}


def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    ALLOWED_MODULES = {
        "math",
        "random"
    }

    if name in ALLOWED_MODULES:
        return __import__(name, globals, locals, fromlist, level)

    raise ImportError(f"Module '{name}' is not allowed")


def get_sandbox_globals():
    safe_builtins = {
        "__import__": safe_import,
        "print": print,
        "range": range,
        "len": len,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
    }

    return {
        "__builtins__": safe_builtins
    }