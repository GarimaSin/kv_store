# Scalable Key-Value Store (Python)

This project implements a production-minded, horizontally scalable Key-Value store prototype.
It includes:

- Thread-safe in-memory store with TTL support and optional persistence to SQLite.
- Pluggable storage backends (In-memory, SQLite).
- Simple HTTP replication for leader->followers (push-based eventual consistency).
- FastAPI server exposing a Redis-like REST API (GET/PUT/DELETE) and management endpoints.
- CLI client for manual testing.
- Unit tests using pytest.

Design notes / limitations
- This is meant as a learning / prototype project. The replication is push-based and simple
  (leader forwards writes to configured follower URLs synchronously or asynchronously).
- For production-grade consensus/replication use Raft/Paxos/CRDTs and robust failure handling.
- The store supports TTL (expires keys) and optional persistence to SQLite for durability.

Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run single-node server (no replication)
uvicorn server:app --reload --port 8000

# Test changes - Please submit changes through a pull request

# Run tests
python -m pytest -q
```

CI preparation
- Use Python 3.12 and install dependencies from `requirements.txt`.
- Run `python -m pytest -q` from the repository root.
- The prepared sample artifact input is `ci/sample-artifact.txt`.

Example API (HTTP):
- PUT /kv/{key}  body: raw value or JSON {"value": "...", "ttl": seconds}
- GET /kv/{key}  -> 200 with raw value, or 404
- DELETE /kv/{key} -> 200 on success
- POST /admin/replicas -> add follower URL for replication
- GET /admin/health -> simple health check
