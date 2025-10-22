"""Simple SQLite persistence for durability. Stores values as BLOB along with ttl info."""
import sqlite3, time, threading

class SQLitePersistence:
    def __init__(self, filename='kv_store.db'):
        self.filename = filename
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock, sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value BLOB, expires_at REAL)''')
            conn.commit()

    def save(self, key: str, value: bytes, ttl: float = None):
        expires_at = None
        if ttl is not None:
            expires_at = time.time() + float(ttl)
        with self._lock, sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('REPLACE INTO kv (key, value, expires_at) VALUES (?, ?, ?)', (key, value, expires_at))
            conn.commit()

    def load_all(self):
        with self._lock, sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('SELECT key, value, expires_at FROM kv')
            rows = c.fetchall()
            now = time.time()
            result = {}
            for k, v, exp in rows:
                if exp is None or exp > now:
                    result[k] = (v, exp)
            return result

    def delete(self, key: str):
        with self._lock, sqlite3.connect(self.filename) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM kv WHERE key=?', (key,))
            conn.commit()
