# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as E
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_academic.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
PANDOC = os.environ.get('PANDOC', 'pandoc')


class AcademicTests(unittest.TestCase):
    def test_word_separation_independent_of_footnote_length(self):
        for note in ['Three note words.', 'Extra explanatory words belong only in this footnote.']:
            ast = json.loads(subprocess.run([PANDOC, '-f', 'markdown', '-t', 'json'],
                input=f'---\ntitle: Excluded title\n---\n# Heading\n\nTwo words.^[{note}]',
                text=True, capture_output=True, check=True).stdout)
            counts = builder.word_counts(ast, PANDOC)
            self.assertEqual(counts['main_text_words'], 3)
            self.assertEqual(counts['footnote_words'], len(note.split()))
            self.assertEqual(counts['footnotes'], 1)

    def test_configurable_font_size_note_size_and_margins(self):
        with tempfile.TemporaryDirectory() as temp:
            for size, note_size, margin in [(12, 10, 1), (11, 9, .8), (13, 11, 1.25)]:
                ref = Path(temp) / f'ref-{size}.docx'
                builder.reference_docx(PANDOC, ref, 'Times New Roman', size, note_size, margin)
                with zipfile.ZipFile(ref) as z:
                    styles = E.fromstring(z.read('word/styles.xml'))
                    body = styles.find("w:style[@w:styleId='BodyText']", builder.NS)
                    note = styles.find("w:style[@w:styleId='FootnoteText']", builder.NS)
                    self.assertEqual(body.find('w:rPr/w:sz', builder.NS).get(builder.W + 'val'), str(size * 2))
                    self.assertEqual(note.find('w:rPr/w:sz', builder.NS).get(builder.W + 'val'), str(note_size * 2))
                    self.assertEqual(body.find('w:pPr/w:spacing', builder.NS).get(builder.W + 'line'), '480')
                    self.assertEqual(note.find('w:pPr/w:spacing', builder.NS).get(builder.W + 'line'), '240')
                    doc = E.fromstring(z.read('word/document.xml'))
                    self.assertEqual(doc.find('.//w:pgMar', builder.NS).get(builder.W + 'left'), str(round(margin * 1440)))
                    self.assertEqual(body.find('w:rPr/w:rFonts', builder.NS).get(builder.W + 'ascii'), 'Times New Roman')

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'edited.docx'; marker.write_bytes(b'edited draft')
            result = subprocess.run(['python3', ROOT / 'scripts/build_academic.py', '--output', temp, '--font', 'Liberation Serif'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('fresh output directory', result.stderr)
            self.assertEqual(marker.read_bytes(), b'edited draft')

    def test_missing_font_fails_without_creating_an_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'candidate'
            result = subprocess.run(['python3', ROOT / 'scripts/build_academic.py', '--output', out,
                                     '--font', 'Deliberately Missing Academic Font 98765'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('is unavailable', result.stderr)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
