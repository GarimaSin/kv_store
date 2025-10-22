"""Thread-safe in-memory key-value store with TTL and optional persistence hooks."""
import threading
import time

class InMemoryStore:
    def __init__(self, persistence=None, cleanup_interval=1.0):
        """Create the store.
        :param persistence: optional object with save(key, value, ttl) and delete(key) methods
        :param cleanup_interval: seconds between TTL cleanup runs
        """
        self._data = {}  # key -> (value, expires_at or None)
        self._lock = threading.RLock()
        self._persistence = persistence
        self._cleanup_interval = cleanup_interval
        self._stop = False
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()

    def _cleanup_loop(self):
        while not self._stop:
            now = time.time()
            to_delete = []
            with self._lock:
                for k, (v, exp) in list(self._data.items()):
                    if exp is not None and exp <= now:
                        to_delete.append(k)
                for k in to_delete:
                    self._data.pop(k, None)
                    if self._persistence:
                        try:
                            self._persistence.delete(k)
                        except Exception:
                            pass
            time.sleep(self._cleanup_interval)

    def put(self, key: str, value: bytes, ttl: float = None):
        """Store raw bytes. ttl in seconds (optional)."""
        expires_at = None
        if ttl is not None:
            expires_at = time.time() + float(ttl)
        with self._lock:
            self._data[key] = (value, expires_at)
            if self._persistence:
                self._persistence.save(key, value, ttl)

    def get(self, key: str):
        with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None
            value, exp = entry
            if exp is not None and exp <= time.time():
                # expired; remove and persist delete
                self._data.pop(key, None)
                if self._persistence:
                    try:
                        self._persistence.delete(key)
                    except Exception:
                        pass
                return None
            return value

    def delete(self, key: str):
        with self._lock:
            existed = self._data.pop(key, None) is not None
            if existed and self._persistence:
                try:
                    self._persistence.delete(key)
                except Exception:
                    pass
            return existed

    def keys(self):
        with self._lock:
            return list(self._data.keys())

    def stop(self):
        self._stop = True
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
