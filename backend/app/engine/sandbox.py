SAFE_BUILTINS = {
    "print": print, "input": input,
    "range": range, "len": len, "enumerate": enumerate, "zip": zip,
    "int": int, "float": float, "str": str, "bool": bool,
    "list": list, "dict": dict, "set": set, "tuple": tuple,
    "sorted": sorted, "abs": abs, "min": min, "max": max, "sum": sum,
    "any": any, "all": all, "round": round,
    "isinstance": isinstance, "type": type, "callable": callable,
    "hasattr": hasattr, "getattr": getattr,
    "reversed": reversed, "map": map, "filter": filter,
    "chr": chr, "ord": ord, "repr": repr,
    "iter": iter, "next": next,
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
        "__build_class__": __build_class__,
        # Types & constructors
        "int": int, "float": float, "str": str, "bool": bool,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "frozenset": frozenset, "complex": complex,
        "bytes": bytes, "bytearray": bytearray, "object": object,
        # I/O
        "print": print, "input": input,
        # Iteration & ranges
        "range": range, "enumerate": enumerate, "zip": zip,
        "map": map, "filter": filter, "iter": iter, "next": next,
        "reversed": reversed,
        # Aggregation
        "len": len, "sum": sum, "min": min, "max": max,
        "abs": abs, "round": round,
        "sorted": sorted, "any": any, "all": all,
        # Type checking
        "isinstance": isinstance, "issubclass": issubclass,
        "type": type, "callable": callable,
        "hasattr": hasattr, "getattr": getattr, "setattr": setattr,
        # String / char
        "chr": chr, "ord": ord, "repr": repr, "format": format,
        "hex": hex, "oct": oct, "bin": bin,
        # Numeric
        "pow": pow, "divmod": divmod,
        # Identity
        "id": id, "hash": hash,
        # Exceptions (needed for try/except in user code)
        "Exception": Exception, "ValueError": ValueError,
        "TypeError": TypeError, "IndexError": IndexError,
        "KeyError": KeyError, "AttributeError": AttributeError,
        "RuntimeError": RuntimeError, "StopIteration": StopIteration,
        "ZeroDivisionError": ZeroDivisionError,
        "NotImplementedError": NotImplementedError,
        "OverflowError": OverflowError,
        # OOP
        "super": super, "property": property,
        "staticmethod": staticmethod, "classmethod": classmethod,
        # Misc
        "slice": slice,
    }

    return {
        "__builtins__": safe_builtins,
        "__name__": "__main__"
    }