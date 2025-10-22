"""Simple replicator that forwards writes to follower HTTP endpoints.
This is intentionally straightforward: it posts write operations to configured follower URLs.
Followers should expose the same /kv endpoints and accept a special header X-Replicated to avoid loops.
"""
import requests, threading, json

class Replicator:
    def __init__(self, followers=None, async_mode=True, timeout=2.0):
        self.followers = followers or []  # list of base URLs like http://host:port
        self.async_mode = async_mode
        self.timeout = timeout

    def add_follower(self, url: str):
        if url not in self.followers:
            self.followers.append(url)

    def remove_follower(self, url: str):
        if url in self.followers:
            self.followers.remove(url)

    def replicate_put(self, key: str, value: bytes, ttl=None):
        payload = value
        headers = {'X-Replicated': '1'}
        params = {}
        if ttl is not None:
            params['ttl'] = str(ttl)
        def do_post(url):
            try:
                requests.put(f"{url}/kv/{key}", data=payload, headers=headers, params=params, timeout=self.timeout)
            except Exception:
                pass
        for f in list(self.followers):
            if self.async_mode:
                threading.Thread(target=do_post, args=(f,), daemon=True).start()
            else:
                do_post(f)

    def replicate_delete(self, key: str):
        headers = {'X-Replicated': '1'}
        def do_delete(url):
            try:
                requests.delete(f"{url}/kv/{key}", headers=headers, timeout=self.timeout)
            except Exception:
                pass
        for f in list(self.followers):
            if self.async_mode:
                threading.Thread(target=do_delete, args=(f,), daemon=True).start()
            else:
                do_delete(f)
