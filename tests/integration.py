#!/usr/bin/env python3
# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
"""Real DOCX/PDF builds, altered layout and a footnote spanning PDF pages."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('INTEGRATION_OUT', str(ROOT / 'build/integration'))).resolve()


def build(name, *args):
    subprocess.run([sys.executable, ROOT / 'scripts/build_academic.py', '--output', OUT / name,
                    '--font', 'Liberation Serif', *args], check=True)
    path = OUT / name
    for i, page in enumerate(pymupdf.open(path / 'paper.pdf'), 1):
        page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(path / f'page-{i}.png')
    return json.loads((path / 'verification.json').read_text())


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    original = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (ROOT / 'sample').iterdir() if p.is_file()}
    demo = build('demo')
    altered = build('altered', '--size', '11', '--note-size', '9', '--margin', '.8')
    assert demo['native_docx_footnotes'] == altered['native_docx_footnotes'] == 20
    assert [n['docx_text'] for n in demo['notes']] == [n['docx_text'] for n in altered['notes']]
    # A long ordinary note forces continuation, followed by a supra target and
    # enough body text to check page numbering independently of word totals.
    source = OUT / 'long-note.md'
    prose = 'This fictional explanation contains several ordinary words for testing a continued footnote. '
    source.write_text('First.[@book, 12]\n\nSecond.[^long]\n\n'
        + ('This is fictional main text for pagination. ' * 350)
        + '\n\nThird.[@book, 20]\n\n[^long]: ' + prose * 100 + ' [@case, para. 24]\n')
    long = build('long-note', '--source', str(source))
    assert long['pdf_pages'] > 2
    assert long['native_docx_footnotes'] == 3
    assert long['notes'][1]['pages_containing_complete_note'] == [], 'Long note did not span pages'
    assert 'supra note 1' in long['notes'][2]['docx_text']
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in original.items())
    results = {name: json.loads((OUT / name / 'verification.json').read_text()) for name in ['demo', 'altered', 'long-note']}
    (OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print('Integration PASS: native notes, PDF references/content/order, altered layout, split note, preserved inputs.')


if __name__ == '__main__':
    main()
