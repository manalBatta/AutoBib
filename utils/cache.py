import os
import json
import hashlib
from config.settings import CACHE_DIR

os.makedirs(CACHE_DIR, exist_ok=True)

def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def load_from_cache(url: str):
    path = os.path.join(CACHE_DIR, cache_key(url) + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    return None

def dump_to_cache(url: str, payload: dict) -> None:
    path = os.path.join(CACHE_DIR, cache_key(url) + ".json")
    json.dump(payload, open(path, "w"), indent=2)
