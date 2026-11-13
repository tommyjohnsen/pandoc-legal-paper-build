#!/usr/bin/env python3
# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
"""Fetch checksum-locked legacy styles atomically; validate cached files too."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    dest = Path(sys.argv[1]); dest.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / 'tools/styles.lock.json').read_text())
    for artifact in lock['downloads']:
        target = dest / artifact['target']
        data = target.read_bytes() if target.exists() else urllib.request.urlopen(artifact['url']).read()
        if hashlib.sha256(data).hexdigest() != artifact['sha256']:
            raise SystemExit(f'Checksum mismatch: {target}; remove the corrupt cache and retry. No style accepted.')
        if not target.exists():
            temp = target.with_suffix(target.suffix + '.partial'); temp.write_bytes(data); temp.replace(target)
        if artifact['target'] == 'modules.tar.gz':
            modules = dest / 'modules'; modules.mkdir(exist_ok=True)
            with tarfile.open(fileobj=io.BytesIO(data)) as tar:
                for member in tar.getmembers():
                    name = Path(member.name).name
                    if name.startswith('juris-us') and name.endswith('.csl') and member.isfile():
                        content = tar.extractfile(member).read()
                        target = modules / name
                        if target.exists() and target.read_bytes() != content:
                            raise SystemExit(f'Modified module: {target}; choose a fresh BUILD directory.')
                        if not target.exists():
                            target.write_bytes(content)
            (modules / '.ok').touch()


if __name__ == '__main__':
    main()
