"""Check the source files needed for this repository's CI training sample."""

from pathlib import Path


repo_root = Path(__file__).resolve().parents[1]
required_files = ("README.md", "kvstore/store.py", "tests/test_store.py")
missing = [name for name in required_files if not (repo_root / name).is_file()]
if missing:
    raise SystemExit("Missing required source files: " + ", ".join(missing))

print("CI smoke check passed: all 3 required source files are present.")
