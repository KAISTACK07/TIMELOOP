"""Serialization utilities for safe conversion of Python values to JSON-compatible types."""


def safe_serialize(value):
    """
    Convert a Python value into a JSON-safe representation.
    Handles primitives, collections, and falls back to str() for unknown types.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [safe_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(k): safe_serialize(v) for k, v in value.items()}
    if isinstance(value, set):
        return [safe_serialize(item) for item in value]
    return str(value)
