#!/usr/bin/env python3
# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
"""Pinned user-local setup, Linux x86_64. Does not install system packages."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import urllib.request
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.tools'


def fetch(url, sha, target):
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == sha:
        return
    temp = target.with_suffix(target.suffix + '.partial')
    urllib.request.urlretrieve(url, temp)
    if hashlib.sha256(temp.read_bytes()).hexdigest() != sha:
        temp.unlink()
        raise ValueError(f'Checksum mismatch for {url}; no unverified file installed')
    temp.replace(target)


def main():
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise SystemExit('Pinned bootstrap supports Linux x86_64. Use the documented amd64 container on other platforms.')
    DEST.mkdir(exist_ok=True)
    lock = json.loads((ROOT / 'tools/dependencies.lock.json').read_text())
    for artifact in lock['archives']:
        archive = DEST / artifact['filename']
        fetch(artifact['url'], artifact['sha256'], archive)
        if archive.suffix == '.deb':
            subprocess.run(['dpkg-deb', '-x', archive, DEST / 'fonts'], check=True)
        else:
            with tarfile.open(archive) as tar:
                tar.extractall(DEST, filter='data')
    (DEST / 'bin').mkdir(exist_ok=True)
    links = {'pandoc': '../pandoc-3.6.4/bin/pandoc', 'tectonic': '../tectonic'}
    for name, target in links.items():
        p = DEST / 'bin' / name
        if not p.exists():
            p.symlink_to(target)
    fc = E.Element('fontconfig')
    E.SubElement(fc, 'include').text = '/etc/fonts/fonts.conf'
    E.SubElement(fc, 'dir').text = str(DEST / 'fonts/usr/share/fonts')
    E.SubElement(fc, 'cachedir').text = str(DEST / 'font-cache')
    E.ElementTree(fc).write(DEST / 'fonts.conf', encoding='utf-8', xml_declaration=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--target', DEST / 'python', '--require-hashes', '-r', ROOT / 'requirements.txt'], check=True)
    env = dict(os.environ, PATH=str(DEST / 'node-v22.14.0-linux-x64/bin') + ':' + os.environ['PATH'], npm_config_cache=str(DEST / 'npm-cache'))
    subprocess.run([DEST / 'node-v22.14.0-linux-x64/bin/npm', 'ci', '--no-audit', '--no-fund'], cwd=ROOT, env=env, check=True)
    print('Setup complete. In bash: source tools/env.sh; make test; make demo')


if __name__ == '__main__':
    main()
