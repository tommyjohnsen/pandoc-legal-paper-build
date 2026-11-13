#!/usr/bin/env python3
# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for name, expected in json.loads((ROOT / 'vendor/checksums.json').read_text()).items():
    actual = hashlib.sha256((ROOT / 'vendor' / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f'Vendor checksum mismatch: {name}. Inspect changes and deliberately update the lock.')
print('All vendored style, locale and font checksums match.')
