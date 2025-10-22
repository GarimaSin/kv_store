import time
from kvstore.store import InMemoryStore
from kvstore.persistence import SQLitePersistence
import os

def test_put_get_delete():
    s = InMemoryStore()
    s.put('a','1'.encode())
    assert s.get('a') == b'1'
    assert s.delete('a') == True
    assert s.get('a') is None

def test_ttl_expiry():
    s = InMemoryStore(cleanup_interval=0.1)
    s.put('k', b'v', ttl=0.5)
    assert s.get('k') == b'v'
    time.sleep(0.7)
    assert s.get('k') is None

def test_persistence_roundtrip(tmp_path):
    db = tmp_path / 'kvtest.db'
    p = SQLitePersistence(str(db))
    s = InMemoryStore(persistence=p)
    s.put('x', b'yy', ttl=1.0)
    # ensure persisted
    loaded = p.load_all()
    assert 'x' in loaded
    s.delete('x')
    assert 'x' not in p.load_all()
