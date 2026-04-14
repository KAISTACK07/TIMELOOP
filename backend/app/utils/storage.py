import os
import json

BASE_DIR = os.path.join(os.path.dirname(__file__), "../../sessions")
os.makedirs(BASE_DIR, exist_ok=True)


def save_session(session_id: str, data: dict):
    path = os.path.join(BASE_DIR, f"{session_id}.json")
    temp_path = path + ".tmp"

    try:
        with open(temp_path, "w") as f:
            json.dump(data, f)

        os.replace(temp_path, path)

    except Exception:
        pass   # don't crash system


def load_session(session_id: str):
    path = os.path.join(BASE_DIR, f"{session_id}.json")

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
            return json.load(f)

    except json.JSONDecodeError:
        return None   # corrupted file → ignore