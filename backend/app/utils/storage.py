import os
import json

BASE_DIR = "sessions"

os.makedirs(BASE_DIR, exist_ok=True)


def save_session(session_id: str, data: dict):
    path = os.path.join(BASE_DIR, f"{session_id}.json")
    with open(path, "w") as f:
        json.dump(data, f)


def load_session(session_id: str):
    path = os.path.join(BASE_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)