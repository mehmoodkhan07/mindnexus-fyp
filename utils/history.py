import json
import os

BASE_PATH = "data/chat_history"
os.makedirs(BASE_PATH, exist_ok=True)

def load_history(username):
    file = f"{BASE_PATH}/{username}.json"
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return []

def save_message(username, role, content):
    history = load_history(username)
    history.append({"role": role, "content": content})
    with open(f"{BASE_PATH}/{username}.json", "w") as f:
        json.dump(history, f, indent=2)