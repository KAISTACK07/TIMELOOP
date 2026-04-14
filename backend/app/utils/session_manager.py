from app.utils.storage import load_session
from app.store import SESSION_STORE   # adjust path if needed


def get_session(session_id: str):
    # 1. Try memory first (fast)
    session = SESSION_STORE.get(session_id)
    if session:
        return session

    # 2. Fallback to disk
    session = load_session(session_id)
    if session:
        SESSION_STORE[session_id] = session
        return session

    return None