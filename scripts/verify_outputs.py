#!/usr/bin/env python3
# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
"""Inspect the exported files: native notes, content, sequence, PDF pagination."""
import json
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as E
import zipfile
import pymupdf

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def normalized(s):
    # Ignore typography-only ligatures, discretionary hyphens and whitespace.
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s)).replace('\u00ad', '').replace('–', '-').replace('—', '-')


def verify(directory):
    with zipfile.ZipFile(directory / 'paper.docx') as z:
        doc = E.fromstring(z.read('word/document.xml'))
        foot = E.fromstring(z.read('word/footnotes.xml'))
        rels = E.fromstring(z.read('word/_rels/document.xml.rels'))
        assert any(r.get('Type', '').endswith('/footnotes') and r.get('Target') == 'footnotes.xml' for r in rels), 'Missing footnote relationship'
        assert not doc.findall('.//' + W + 'endnoteReference'), 'Unexpected endnotes'
        refs = [x.get(W + 'id') for x in doc.iter(W + 'footnoteReference')]
        native = [x for x in foot if x.tag == W + 'footnote' and not x.get(W + 'type')]
        ids = [x.get(W + 'id') for x in native]
        assert refs == ids and len(ids) == len(set(ids)), 'Footnote ids/order do not connect'
        assert len(ids) == json.loads((directory / 'citations.json').read_text())['notes']
        for note in native:
            assert len(list(note.iter(W + 'footnoteRef'))) == 1, 'Footnote missing its native marker'
        texts = [''.join(x.text or '' for x in note.iter(W + 't')) for note in native]
        # TeX's small-cap glyphs extract as uppercase; Word keeps source case and
        # applies the smallCaps run property. Normalize only those explicit runs.
        pdf_expected = []
        for note in native:
            chunks = []
            for run in note.iter(W + 'r'):
                text = ''.join(x.text or '' for x in run.iter(W + 't'))
                if run.find(W + 'rPr/' + W + 'smallCaps') is not None:
                    text = text.upper()
                chunks.append(text)
            pdf_expected.append(''.join(chunks))
        note_ast = []
        def collect_notes(node):
            if isinstance(node, list):
                for child in node:
                    collect_notes(child)
            elif isinstance(node, dict):
                if node.get('t') == 'Note':
                    note_ast.append(node['c'])
                else:
                    for child in node.values():
                        collect_notes(child)
        collect_notes(json.loads((directory / 'resolved.json').read_text())['blocks'])
        resolved = json.dumps(note_ast)
        if '"Emph"' in resolved:
            assert list(foot.iter(W + 'i')), 'Expected academic italics'
        if '"SmallCaps"' in resolved:
            assert list(foot.iter(W + 'smallCaps')), 'Expected native small capitals'
    pdf = pymupdf.open(directory / 'paper.pdf')
    page_texts = [p.get_text(sort=True) for p in pdf]
    # Isolate footnote regions by the standard TeX separator. This handles notes
    # split across pages without mixing intervening main text or page numbers.
    settings = json.loads((directory / 'layout-settings.json').read_text())
    margin = settings['margin'] * 72
    note_pages, body_markers = [], []
    for page in pdf:
        rules = [d['rect'].y0 for d in page.get_drawings()
                 if abs(d['rect'].x0 - margin) < .2 and abs(d['rect'].height) < .1
                 and abs(d['rect'].width - .4 * (612 - 2 * margin)) < .2]
        boundary = min(rules) if rules else page.rect.height - margin
        clip = pymupdf.Rect(margin - 1, boundary + .5, 612 - margin + 1, 792 - margin + 2)
        # TeX emits these regions in logical order. MuPDF's geometric re-sort
        # can interleave justified text around a superscript on long notes.
        note_pages.append(page.get_text('text', clip=clip, sort=False,
                          flags=pymupdf.TEXTFLAGS_TEXT | pymupdf.TEXT_DEHYPHENATE) if rules else '')
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    if span['bbox'][3] < boundary and span['flags'] & 1 and span['text'].isdigit():
                        body_markers.append(int(span['text']))
    assert body_markers == list(range(1, len(texts) + 1)), 'PDF main-text note references disagree with native DOCX'
    alltext = normalized('\n'.join(note_pages))
    position = 0
    matches = []
    for number, text in enumerate(pdf_expected, 1):
        target = normalized(str(number) + text)
        found = alltext.find(target, position)
        assert found >= 0, f'PDF note {number} numbering/content mismatch: {text[:180]}'
        position = found + len(target)
        page_numbers = [i + 1 for i, t in enumerate(note_pages) if normalized(text) in normalized(t)]
        matches.append({'number': number, 'pages_containing_complete_note': page_numbers, 'docx_text': texts[number - 1], 'pdf_expected_text': text})
    assert alltext == ''.join(normalized(str(i) + text) for i, text in enumerate(pdf_expected, 1)), 'Unexpected/missing PDF footnote text'
    assert all(p.rect.width == 612 and p.rect.height == 792 for p in pdf), 'Expected configured letter pages'
    missing = [i + 1 for i, t in enumerate(page_texts) if '\ufffd' in t]
    assert not missing, f'Missing glyphs on pages {missing}'
    for i, p in enumerate(pdf):
        for word in p.get_text('words'):
            assert word[0] >= 0 and word[1] >= 0 and word[2] <= p.rect.width and word[3] <= p.rect.height, f'Text outside page {i + 1}'
    result = {'native_docx_footnotes': len(ids), 'connected_ids': ids, 'pdf_pages': len(pdf),
              'pdf_main_text_note_references': body_markers,
              'pdf_note_sequence_and_text_match_docx': True, 'notes': matches,
              'comparison': 'Note numbers, order and text match after whitespace/ligature normalization and uppercasing only DOCX smallCaps runs to match PDF glyph extraction. Line wrapping, page breaks and small-cap glyph design may differ; Word pagination was not measured.',
              'visual_review': 'PENDING: render all pages and inspect before relying on this output.'}
    (directory / 'verification.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(f'Verified {len(ids)} native footnotes; PDF {len(pdf)} pages; citation text and sequence agree.')
    return result


if __name__ == '__main__':
    verify(Path(sys.argv[1]))
