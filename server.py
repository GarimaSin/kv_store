"""FastAPI server exposing a simple KV REST API and admin endpoints for replication."""
from fastapi import FastAPI, Response, Request, HTTPException
from pydantic import BaseModel
import os
from kvstore.store import InMemoryStore
from kvstore.persistence import SQLitePersistence
from kvstore.replication import Replicator

# configure persistence if DB path provided
DB = os.environ.get('KV_DB', None)
persistence = SQLitePersistence(DB) if DB else None

# load initial data from persistence if present
store = InMemoryStore(persistence=persistence) if persistence else InMemoryStore()
if persistence:
    rows = persistence.load_all()
    for k, (v, exp) in rows.items():
        # store raw bytes and keep original TTL (approx)
        ttl = None
        if exp is not None:
            import time
            ttl = max(0, exp - time.time())
        store.put(k, v, ttl=ttl)

replicator = Replicator(followers=[], async_mode=True)

app = FastAPI(title='KV Store')

class PutBody(BaseModel):
    value: bytes = None
    ttl: float = None

@app.put('/kv/{key}')
async def put_key(key: str, request: Request):
    # avoid replicating replicated requests
    if request.headers.get('x-replicated') == '1':
        body = await request.body()
        store.put(key, body)
        return {'status': 'ok'}
    # normal request: accept json or raw body
    content_type = request.headers.get('content-type', 'application/octet-stream')
    if content_type.startswith('application/json'):
        data = await request.json()
        value = data.get('value', '').encode('utf-8') if isinstance(data.get('value',''), str) else data.get('value')
        ttl = data.get('ttl', None)
    else:
        body = await request.body()
        value = body
        ttl = None
        if 'ttl' in request.query_params:
            try:
                ttl = float(request.query_params['ttl'])
            except Exception:
                ttl = None
    store.put(key, value, ttl=ttl)
    # replicate to followers (fire-and-forget by default)
    replicator.replicate_put(key, value, ttl=ttl)
    return {'status': 'ok'}

@app.get('/kv/{key}')
async def get_key(key: str):
    v = store.get(key)
    if v is None:
        raise HTTPException(status_code=404, detail='key not found')
    # return raw bytes with octet-stream
    return Response(content=v, media_type='application/octet-stream')

@app.delete('/kv/{key}')
async def delete_key(key: str, request: Request):
    existed = store.delete(key)
    # replicate delete
    replicator.replicate_delete(key)
    return {'deleted': existed}

class RepSpec(BaseModel):
    url: str

@app.post('/admin/replicas')
async def add_replica(spec: RepSpec):
    replicator.add_follower(spec.url)
    return {'followers': replicator.followers}

@app.get('/admin/replicas')
async def list_replicas():
    return {'followers': replicator.followers}

@app.delete('/admin/replicas')
async def remove_replica(spec: RepSpec):
    replicator.remove_follower(spec.url)
    return {'followers': replicator.followers}

@app.get('/admin/health')
async def health():
    return {'status': 'ok'}
