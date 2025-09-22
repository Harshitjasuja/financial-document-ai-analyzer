# src/storage.py
import json
from pathlib import Path
import threading
import time

DATA_DIR = Path("data/processed")
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

QUERIES_LOG = LOGS_DIR / "queries.jsonl"
STATS_FILE = DATA_DIR / "stats.json"

_lock = threading.Lock()

def append_query_log(entry: dict):
    entry = dict(entry)
    entry["ts"] = entry.get("ts") or time.time()
    with _lock:
        with open(QUERIES_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def read_recent_queries(limit=50):
    if not QUERIES_LOG.exists():
        return []
    with _lock:
        lines = QUERIES_LOG.read_text(encoding="utf-8").splitlines()
    items = [json.loads(l) for l in lines if l.strip()]
    return list(reversed(items))[:limit]

def increment_counter(key: str, by: int = 1):
    stats = read_stats()
    stats[key] = int(stats.get(key, 0)) + by
    write_stats(stats)

def read_stats():
    if not STATS_FILE.exists():
        return {}
    with _lock:
        try:
            return json.loads(STATS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

def write_stats(obj: dict):
    with _lock:
        STATS_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
