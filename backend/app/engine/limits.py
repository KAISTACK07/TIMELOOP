MAX_STEPS = 20000
MAX_DEPTH = 1000
MAX_CONTAINER_ITEMS = 50
MAX_SERIALIZATION_DEPTH = 4

# Mode-aware execution timeouts (seconds)
EXECUTION_TIMEOUTS = {
    "reduced": 30,
    "smart": 10,
    "detailed": 5,
}

EXECUTION_TIMEOUT = 8  # legacy default


def get_timeout(mode: str) -> int:
    return EXECUTION_TIMEOUTS.get(mode, EXECUTION_TIMEOUT)