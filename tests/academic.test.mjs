// PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { prepare, validateItems } from '../scripts/academic.mjs';

const root = path.resolve(import.meta.dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'sample/academic-references.json')));
const style = fs.readFileSync(path.join(root, 'vendor/academic-legal.csl'), 'utf8');
const locale = fs.readFileSync(path.join(root, 'vendor/locales-en-US.xml'), 'utf8');
const pandoc = process.env.PANDOC || 'pandoc';
function ast(markdown) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'academic-test-'));
  try {
    const file = path.join(dir, 'input.md'); fs.writeFileSync(file, markdown);
    const result = spawnSync(pandoc, [file, '-f', 'markdown', '-t', 'json'], { encoding: 'utf8', timeout: 10000 });
    assert.equal(result.status, 0, result.stderr);
    return JSON.parse(result.stdout);
  } finally { fs.rmSync(dir, { recursive: true }); }
}
const render = (md, refs = data) => prepare(ast(md), refs, style, locale, pandoc);
const text = html => html.replace(/<[^>]*>/g, '');

test('synthetic corpus: all seven source classes, native note graph, stable Id/supra targets', () => {
  const result = render(fs.readFileSync(path.join(root, 'sample/academic.md'), 'utf8'));
  const notes = result.audit.clusters.map(c => text(c.html));
  assert.equal(result.audit.notes, 20);
  assert.equal(notes.length, 20); // One prose-only note and one two-cluster note.
  assert.match(notes[0], /88 W\. App\. R\. 201, 214 \(Westmarch Ct\. App\. 2022\)/);
  assert.equal(notes[1], 'Id. at 215.');
  assert.equal(notes[2], 'Id.');
  assert.match(notes[5], /supra note 4 at 92/);
  assert.match(notes[6], /Westmarch Code § 4\(a\)\(2\) \(official ed\. 2025\)/);
  assert.match(notes[7], /9 Westmarch Admin\. Code § 12\.3\(b\)/);
  assert.match(notes[8], /Westmarch Bar Ethics Comm\..*Formal Op\. 26-01.*para\. 7/);
  assert.match(notes[9], /https:\/\/example\.org\/fictional-notice/);
  assert.match(notes[10], /supra note 5 at 15–17/);
  assert.match(notes[11], /Harlow, 88 W\. App\. R\. at 219/);
  assert.match(notes[12], /^see Harlow.*discussing timing; cf\. Adaeze Okafor/);
  assert.match(notes[16], /chap\. 2 \(2nd ed\. 2018\)/);
  assert.match(notes[17], /supra note 5 at 20/);
  assert.match(notes[18], /para\. 24/);
  assert.match(notes[19], /n\. 4/);
  assert.deepEqual(result.audit.sourceMetadata, data);
  const serialized = JSON.stringify(result.ast);
  assert(!serialized.includes('"t":"Cite"'));
  assert(!serialized.includes('__academic_note_barrier__'));
  assert(serialized.includes('"t":"SmallCaps"'));
  assert(serialized.includes('"t":"Emph"'));
});

for (const [locator, expected] of [
  ['12', /12/], ['p. 12', /12/], ['pp. 12--15', /12–15/], ['§ 4(a)(2)', /§ 4\(a\)\(2\)/],
  ['sec. 4', /§ 4/], ['para. 12', /para\. 12/], ['¶ 12', /para\. 12/], ['n. 4', /n\. 4/], ['ch. 2', /chap\. 2/],
]) {
  test(`locator ${locator} survives citation rendering`, () => {
    assert.match(text(render(`Text.[@book, ${locator}]`).audit.clusters[0].html), expected);
  });
}

test('ordinary and inline Markdown notes stay single notes with citations and prose', () => {
  const result = render('One.[^a] Two.^[Explanation [@book, 15]]\n\n[^a]: First [@case, 20] and then [@journal, 88].');
  assert.equal(result.audit.notes, 2);
  assert.deepEqual(result.audit.clusters.map(c => c.note), [1, 1, 2]);
  assert(result.audit.clusters.every(c => !/Id\.|supra/.test(c.html)));
  assert(JSON.stringify(result.ast).includes('Explanation'));
});

test('explanatory-note punctuation preserves sentence continuation and avoids duplicate periods', () => {
  const result = render('Text.^[Compare [@journal, 94] with [@book, 12]. A further sentence.]');
  assert.match(text(result.audit.clusters[0].html), /\(2020\)$/);
  assert.match(text(result.audit.clusters[1].html), /\(2nd ed\. 2018\)\.$/);
  assert(!JSON.stringify(result.ast).includes('"c":"."'));
});

test('prose, multi-authority, affixes and explanatory notes break Id eligibility', () => {
  for (const middle of ['^[Explanation only.]', '^[See [@book, 12] for discussion.]', '[@book, 12; @journal, 88]', '[see @book, 12, discussing examples]']) {
    const result = render(`One.[@book, 12] Two.${middle} Three.[@book, 13]`);
    assert.doesNotMatch(text(result.audit.clusters.at(-1).html), /^Id\./);
  }
});

test('ambiguous same-author works retain full forms and actionable review flags', () => {
  const refs = structuredClone(data);
  refs.push({ ...structuredClone(refs.find(x => x.id === 'book')), id: 'other-book', title: 'Other Imaginary Work' });
  const result = render('One.[@book, 12] Two.[@other-book, 14] Three.[@book, 15]', refs);
  assert(result.audit.clusters.every(c => !/supra|Id\./.test(c.html)));
  assert(result.audit.warnings.some(w => w.code === 'FULL_FORM'));
});

test('case repeat without pinpoint retains full form', () => {
  const result = render('One.[@case, 12] Two.[@book, 15] Three.[@case]');
  assert.match(text(result.audit.clusters[2].html), /Westmarch Ct\. App\. 2022/);
});

test('bar authority is not duplicated by institutional author metadata', () => {
  const refs = structuredClone(data); const bar = refs.find(x => x.id === 'bar');
  bar.author = [{ literal: bar.authority }];
  const result = render('Text.[@bar, para. 7]', refs);
  assert.equal(text(result.audit.clusters[0].html).split(bar.authority).length - 1, 1);
  assert.deepEqual(result.audit.sourceMetadata, refs);
});

for (const [syntax, error] of [
  ['@book', /AuthorInText/], ['[-@book]', /SuppressAuthor/], ['[@unknown]', /Unknown citation key/],
  ['[@book, appendix A]', /unsupported locator/], ['[@book, 12, 14]', /compound locator/],
  ['[*see* @book, 12]', /Rich citation affix/], ['# Title [@book]', /headings/],
  ['Text. <b>raw</b>', /Raw HTML/], ['---\ntitle: "Title [@book]"\n---\nText.', /metadata/],
  ['Text.\n\n| Citation |\n|---|\n| [@book] |', /headings\/captions/],
]) {
  test(`reject ${syntax}`, () => assert.throws(() => render(syntax), error));
}

test('missing legal metadata fails with the key and required field', () => {
  for (const [id, fields] of Object.entries({case: ['jurisdiction', 'authority', 'issued', 'volume', 'container-title', 'page', 'title-short'], statute: ['section', 'edition'], regulation: ['section'], book: ['edition'], bar: ['number']})) {
    for (const field of fields) {
      const refs = structuredClone(data); delete refs.find(x => x.id === id)[field];
      assert.throws(() => validateItems(refs), new RegExp(`${id}: missing metadata ${field}`));
    }
  }
});

test('invalid years, duplicate keys and unsupported source types fail', () => {
  assert.throws(() => validateItems([...data, data[0]]), /Duplicate citation id/);
  assert.throws(() => validateItems([{ ...data[0], issued: { 'date-parts': [['2022']] } }]), /numeric year/);
  assert.throws(() => validateItems([{ ...data[0], type: 'song' }]), /unsupported source type/);
});

test('legacy Juris-M explicitly rejects notes, author modes, prefixes and ambiguous suffixes', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'legacy-citations-'));
  try {
    for (const [md, expected] of [
      ['Text.^[Explanation [@book, 12]]', /does not support footnotes/],
      ['Text.[-@book]', /cannot map mode\/prefix/],
      ['Text.[see @book]', /cannot map mode\/prefix/],
      ['Text.[@book, 12, discussion]', /cannot map suffix/],
    ]) {
      const input = path.join(dir, 'ast.json'); fs.writeFileSync(input, JSON.stringify(ast(md)));
      const result = spawnSync(process.execPath, [path.join(root, 'scripts/render-cslm.mjs'), input,
        path.join(root, 'sample/academic-references.json'), path.join(root, 'vendor/academic-legal.csl'),
        path.join(root, 'vendor/locales-en-US.xml'), dir, path.join(dir, 'out.json')], { encoding: 'utf8' });
      assert.notEqual(result.status, 0);
      assert.match(result.stderr, expected);
    }
  } finally { fs.rmSync(dir, { recursive: true }); }
});
