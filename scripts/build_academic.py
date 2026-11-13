#!/usr/bin/env python3
# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
"""Non-overwriting build of one resolved note graph into DOCX and PDF."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def word_counts(ast, pandoc):
    """Metadata excluded; headings/tables included. Count notes independently."""
    notes = []

    def strip(n):
        if isinstance(n, list):
            return [strip(x) for x in n if not (isinstance(x, dict) and x.get('t') == 'Note' and notes.append(x['c']) is None)]
        if isinstance(n, dict):
            return {k: strip(v) for k, v in n.items()}
        return n

    body = strip(ast['blocks'])

    def count(blocks):
        doc = dict(ast, meta={}, blocks=blocks)
        text = run([pandoc, '-f', 'json', '-t', 'plain', '--wrap=none'], input=json.dumps(doc), text=True, capture_output=True).stdout
        return len(re.findall(r"\b\w+(?:[’'-]\w+)*\b", text, re.UNICODE))

    return {'main_text_words': count(body), 'footnote_words': sum(count(n) for n in notes),
            'footnotes': len(notes), 'method': 'Unicode word tokens; metadata excluded, headings/tables included; notes counted after citation rendering. No page-count inference.'}


def reference_docx(pandoc, output, font, size, note_size, margin):
    raw = run([pandoc, '--print-default-data-file=reference.docx'], capture_output=True).stdout
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files = {n: z.read(n) for n in z.namelist()}
    styles = ET.fromstring(files['word/styles.xml'])
    # Apply the explicit build font to all Word styles, including note text.
    for rp in styles.findall('.//w:rPr', NS):
        f = rp.find('w:rFonts', NS)
        if f is None:
            f = ET.SubElement(rp, W + 'rFonts')
        f.attrib.clear()
        for k in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
            f.set(W + k, font)
    for style in styles.findall('w:style', NS):
        ident = style.get(W + 'styleId')
        if style.get(W + 'type') != 'paragraph':
            continue
        rp = style.find('w:rPr', NS)
        if rp is None:
            rp = ET.SubElement(style, W + 'rPr')
        f = rp.find('w:rFonts', NS)
        if f is None:
            f = ET.SubElement(rp, W + 'rFonts')
        f.attrib.clear()
        for k in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
            f.set(W + k, font)
        # Size is a configurable manuscript choice; the guide did not specify it.
        value = note_size if ident == 'FootnoteText' else size
        for tag in ['sz', 'szCs']:
            e = rp.find('w:' + tag, NS)
            if e is None:
                e = ET.SubElement(rp, W + tag)
            e.set(W + 'val', str(round(value * 2)))
        pp = style.find('w:pPr', NS)
        if pp is None:
            pp = ET.SubElement(style, W + 'pPr')
        sp = pp.find('w:spacing', NS)
        if sp is None:
            sp = ET.SubElement(pp, W + 'spacing')
        sp.attrib.clear()
        for k, v in {'line': '240' if ident == 'FootnoteText' else '480', 'lineRule': 'auto', 'after': '0', 'before': '0'}.items():
            sp.set(W + k, v)
    files['word/styles.xml'] = ET.tostring(styles, encoding='utf-8', xml_declaration=True)
    document = ET.fromstring(files['word/document.xml'])
    section = document.find('.//w:sectPr', NS)
    margins = section.find('w:pgMar', NS)
    if margins is None:
        margins = ET.SubElement(section, W + 'pgMar')
    for k in ['top', 'bottom', 'left', 'right']:
        margins.set(W + k, str(round(margin * 1440)))
    size_el = section.find('w:pgSz', NS)
    if size_el is None:
        size_el = ET.SubElement(section, W + 'pgSz')
    size_el.set(W + 'w', '12240'); size_el.set(W + 'h', '15840')
    files['word/document.xml'] = ET.tostring(document, encoding='utf-8', xml_declaration=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, contents in files.items():
            z.writestr(name, contents)


def build(args):
    pandoc = os.environ.get('PANDOC', 'pandoc')
    run([sys.executable, ROOT / 'scripts/check_vendor.py'])
    node_version = run(['node', '--version'], capture_output=True, text=True).stdout.strip()
    if node_version != 'v22.14.0':
        raise ValueError(f'Expected pinned Node v22.14.0, got {node_version}; source tools/env.sh.')
    version = run([pandoc, '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    if version != 'pandoc 3.6.4':
        raise ValueError(f'Expected pinned pandoc 3.6.4, got {version}')
    if not (4 <= args.size <= 72 and 4 <= args.note_size <= 72 and 0.25 <= args.margin <= 3):
        raise ValueError('Use font sizes 4–72pt and margins 0.25–3in.')
    matched = run(['fc-match', '-f', '%{family}', args.font], capture_output=True, text=True).stdout
    if args.font.casefold() not in [s.strip().casefold() for s in matched.split(',')]:
        raise ValueError(f'Font "{args.font}" is unavailable (fontconfig selected {matched}). Install a lawfully obtained font or explicitly use --font for a demonstration. The guide requires Times New Roman.')
    font_files = set()
    for face in ['Regular', 'Bold', 'Italic', 'Bold Italic']:
        font_files.add(Path(run(['fc-match', '-f', '%{file}', f'{args.font}:style={face}'], capture_output=True, text=True).stdout))
    # Exclusive directory creation protects previous exports and edited drafts.
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source, bib = args.source.resolve(), args.bib.resolve()
    run([pandoc, source, '--fail-if-warnings', '-f', 'markdown', '-t', 'json', '-o', out / 'source.json'])
    # The source and full original metadata are preserved in a private build directory only.
    env = dict(os.environ, PANDOC=pandoc)
    run(['node', ROOT / 'scripts/academic.mjs', out / 'source.json', bib,
         ROOT / 'vendor/academic-legal.csl', ROOT / 'vendor/locales-en-US.xml',
         out / 'resolved.json', out / 'citations.json'], env=env)
    ast = json.loads((out / 'resolved.json').read_text())
    # Author YAML must not override manuscript layout or add raw TeX/Word content.
    ast['meta'] = {k: v for k, v in ast['meta'].items() if k in ['title', 'subtitle', 'author', 'date', 'lang']}
    write_json(out / 'resolved.json', ast)
    counts = word_counts(ast, pandoc)
    write_json(out / 'counts.json', counts)
    write_json(out / 'layout-settings.json', {'font': args.font, 'size': args.size, 'note_size': args.note_size, 'margin': args.margin})
    ref = out / 'reference.docx'
    reference_docx(pandoc, ref, args.font, args.size, args.note_size, args.margin)
    run([pandoc, out / 'resolved.json', '-f', 'json', '--standalone', '--reference-doc', ref, '-o', out / 'paper.docx'])
    # Small capitals use a named, openly licensed companion font in PDF. Word
    # retains native smallCaps properties in the chosen manuscript font.
    header = out / 'layout.tex'
    header.write_text('\\usepackage{setspace}\n\\doublespacing\n'
                      + '\\AtBeginDocument{\\fontsize{' + str(args.size) + '}{' + str(args.size * 1.2) + '}\\selectfont}\n'
                      + '\\makeatletter\n\\renewcommand\\footnotesize{\\@setfontsize\\footnotesize{'
                      + str(args.note_size) + '}{' + str(args.note_size * 1.2) + '}}\n\\makeatother\n')
    texargs = [pandoc, out / 'resolved.json', '-f', 'json', '--standalone', '-t', 'latex',
               '-V', f'mainfont={args.font}', '-V', f'geometry:margin={args.margin}in',
               '-V', 'papersize=letter', '-V', 'mainfontoptions=SmallCapsFont=TeX Gyre Termes,SmallCapsFeatures={Letters=SmallCaps}',
               '-H', header, '-o', out / 'paper.tex']
    run(texargs)
    shutil.copyfile(ROOT / 'vendor/texgyretermes-regular.otf', out / 'texgyretermes-regular.otf')
    # Register the vendored font without changing the user's installed fonts.
    fontconf = ET.Element('fontconfig')
    for folder in sorted({f.parent for f in font_files}):
        ET.SubElement(fontconf, 'dir').text = str(folder)
    ET.SubElement(fontconf, 'dir').text = str(out)
    ET.SubElement(fontconf, 'cachedir').text = str(out / 'font-cache')
    ET.ElementTree(fontconf).write(out / 'fonts.conf', encoding='utf-8', xml_declaration=True)
    engine = os.environ.get('TECTONIC', 'tectonic')
    engine_version = run([engine, '--version'], capture_output=True, text=True).stdout.strip()
    if not engine_version.startswith('tectonic 0.15.0'):
        raise ValueError(f'Expected tectonic 0.15.0, got {engine_version}')
    texenv = dict(os.environ, XDG_CACHE_HOME=os.environ.get('XDG_CACHE_HOME', str(ROOT / 'build/.cache')))
    texenv['FONTCONFIG_FILE'] = str(out / 'fonts.conf')
    run([engine, '--untrusted', '--web-bundle', 'https://relay.fullyjustified.net/default_bundle_v33.tar',
         '--keep-logs', '--keep-intermediates', '--outdir', out, 'paper.tex'], env=texenv, cwd=out)
    bundle_id = '6ffe055852f8faf66c0acbe1a7fb27f87b869a90bad1204f3bf4d9683f597c7c'
    cache = Path(texenv['XDG_CACHE_HOME']) / 'Tectonic/urls/https,58,,47,,47,relay.fullyjustified.net,47,default_bundle_v33.tar'
    if cache.read_text().strip() != bundle_id:
        raise ValueError('TeX bundle identity changed; inspect the upstream revision before updating the lock.')
    # PDF page counts describe this renderer only, not Microsoft Word pagination.
    run([sys.executable, ROOT / 'scripts/verify_outputs.py', out])
    inputs = [source, bib, ROOT / 'vendor/academic-legal.csl', ROOT / 'vendor/locales-en-US.xml', ROOT / 'package-lock.json']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    write_json(out / 'manifest.json', {
        'pandoc': version, 'node': node_version, 'python': sys.version.split()[0], 'tectonic': engine_version, 'font': args.font, 'font_size_pt': args.size,
        'note_size_pt': args.note_size, 'margin_in': args.margin, 'double_spaced_main_text': True,
        'pdf_small_caps_font': 'TeX Gyre Termes', 'guide_font_match': args.font == 'Times New Roman',
        'tex_bundle_id': bundle_id,
        'font_files': {p.name: sha(p) for p in sorted(font_files)},
        'inputs': {str(p.name): sha(p) for p in inputs},
        'build_code': {name: sha(ROOT / name) for name in [
            'scripts/build_academic.py', 'scripts/academic.mjs', 'scripts/verify_outputs.py',
            'scripts/derive_style.py', 'tools/dependencies.lock.json']},
        'outputs': {p.name: sha(p) for p in out.iterdir() if p.is_file()},
        'source_date_epoch': os.environ.get('SOURCE_DATE_EPOCH'),
        'reproducibility': 'Pinned toolchain and shared citation graph; PDF/DOCX container timestamps may differ. See docs/academic.md.',
    })
    print(json.dumps(counts, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT / 'sample/academic.md')
    p.add_argument('--bib', type=Path, default=ROOT / 'sample/academic-references.json')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--font', default='Times New Roman')
    p.add_argument('--size', type=float, default=12, help='Configurable example, not a school requirement')
    p.add_argument('--note-size', type=float, default=10, help='Configurable example, not a school requirement')
    p.add_argument('--margin', type=float, default=1, help='Inches; configurable example, not a school requirement')
    args = p.parse_args()
    try:
        build(args)
    except (ValueError, FileExistsError, subprocess.CalledProcessError) as e:
        p.exit(1, f'Build failed: {e}\nChoose a fresh output directory; partial/previous builds are retained for inspection.\n')


if __name__ == '__main__':
    main()
