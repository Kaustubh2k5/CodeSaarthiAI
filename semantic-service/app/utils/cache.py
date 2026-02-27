import json
import hashlib
import threading
from pathlib import Path
from typing import Optional, Dict, Any

from app.config import settings


class SemanticCache:
    """
    Persistent cache for symbol semantic descriptions.

    Key idea:
    hash(symbol structure) -> semantic output
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.lock = threading.Lock()
        self._cache: Dict[str, Any] = {}

        self._load()

    # -------------------------
    # HASHING
    # -------------------------

    def compute_key(self, symbol) -> str:
        """
        Create deterministic hash based on semantic inputs.
        """

        payload = {
            "name": symbol.name,
            "type": symbol.type,
            "file": symbol.file,
            "language": symbol.language,
            "imports": sorted(symbol.imports),
            "calls": sorted(symbol.calls),
        }

        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    # -------------------------
    # CACHE OPERATIONS
    # -------------------------

    def get(self, key: str) -> Optional[Dict]:
        return self._cache.get(key)

    def set(self, key: str, value: Dict):
        with self.lock:
            self._cache[key] = value
            self._persist()

    # -------------------------
    # DISK IO
    # -------------------------

    def _load(self):
        if not self.path.exists():
            return

        try:
            with open(self.path, "r") as f:
                self._cache = json.load(f)
        except Exception:
            self._cache = {}

    def _persist(self):
        with open(self.path, "w") as f:
            json.dump(self._cache, f)


# singleton cache instance
cache = SemanticCache(settings.CACHE_PATH)