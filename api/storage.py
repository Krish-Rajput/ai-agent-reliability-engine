"""
Minimal JSON-file storage.

A hackathon MVP does not need Postgres. Everything lives in one
`/tmp/db.json`, read fully into memory on each request and written back
atomically. 
"""
from __future__ import annotations
import json
import os
import threading
from typing import Any, Dict

_LOCK = threading.Lock()
# MODIFIED: Pointing to Vercel's temporary writable directory
_PATH = "/tmp/db.json"

_DEFAULT: Dict[str, Any] = {"agents": {}, "scenarios": {}, "results": {}, "runs": {}}


def _ensure_file():
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    if not os.path.exists(_PATH):
        with open(_PATH, "w") as f:
            json.dump(_DEFAULT, f)


def load() -> Dict[str, Any]:
    _ensure_file()
    with _LOCK:
        with open(_PATH, "r") as f:
            return json.load(f)


def save(db: Dict[str, Any]) -> None:
    _ensure_file()
    with _LOCK:
        tmp = _PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(db, f, indent=2)
        os.replace(tmp, _PATH)