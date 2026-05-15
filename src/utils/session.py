import json
import os


def load_settings():
    if os.path.exists("settings.json"):
        try:
            with open("settings.json", "r") as f: return json.load(f)
        except: return {"theme": "dark"}
    return {"theme": "dark"}

def save_settings(settings):
    with open("settings.json", "w") as f:
        json.dump(settings, f)
