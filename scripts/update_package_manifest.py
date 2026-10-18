"""Refresh public release hashes after reviewed source or asset changes."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/package-manifest.json"
files = []
for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or p == OUTPUT or any(part in p.parts for part in (".git", "__pycache__", ".venv", "metastore_db", "spark-warehouse")):
        continue
    relative = p.relative_to(ROOT)
    if relative.parts[0] == "validation" and p.suffix == ".json":
        continue
    if p.name.startswith("local_") and p.suffix in (".html", ".ipynb", ".json"):
        continue
    files.append({"path": relative.as_posix(), "bytes": p.stat().st_size,
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
OUTPUT.write_text(json.dumps({"prepared_on": "2026-10-18", "release": "USD denomination 1.1",
    "scope": "Current release artifacts and explicitly archived provenance; excludes this manifest and mutable validation JSON reports. Original selected input hashes remain separate in source-provenance.json.",
    "files": files}, indent=2) + "\n")
print(f"Hashed {len(files)} public package files")
