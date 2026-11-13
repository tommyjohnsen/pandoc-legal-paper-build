// PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit recorded in Git and .provenance/ledger.jsonl.
// One ordered note graph and citation pass, shared by all output writers.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import CSL from 'citeproc';

export function plain(xs = []) {
  return xs.map(x => {
    if (x.t === 'Str') return x.c;
    if (['Space', 'SoftBreak'].includes(x.t)) return ' ';
    throw Error(`Rich citation affix (${x.t}) is unsupported; put formatted prose outside the citation in a Markdown footnote.`);
  }).join('').replace(/\u00a0/g, ' ');
}

export function citationItem(c) {
  if (c.citationMode.t !== 'NormalCitation') {
    throw Error(`@${c.citationId}: ${c.citationMode.t} is unsupported in academic notes; use [@key] and put narrative author names in prose.`);
  }
  const item = { id: c.citationId };
  const prefix = plain(c.citationPrefix).trim();
  if (prefix) item.prefix = prefix + ' ';
  const s = plain(c.citationSuffix).trim().replace(/^,\s*/, '');
  if (!s) return item;
  const labels = { 'p.': 'page', 'pp.': 'page', 'sec.': 'section', 'secs.': 'section', '§': 'section', '§§': 'section', 'para.': 'paragraph', 'paras.': 'paragraph', '¶': 'paragraph', '¶¶': 'paragraph', 'n.': 'note', 'ch.': 'chapter' };
  // Deliberately bounded grammar: comma lists and compound locators require prose.
  const m = s.match(/^(?:(pp?\.|secs?\.|§§?|paras?\.|¶¶?|n\.|ch\.)\s*)?([0-9]+[A-Za-z]?(?:\.[0-9]+)*(?:\([A-Za-z0-9]+\))*(?:[-–][0-9]+[A-Za-z]?(?:\.[0-9]+)*(?:\([A-Za-z0-9]+\))*)?)(?:,\s+(.+))?$/u);
  if (!m) throw Error(`@${c.citationId}: unsupported locator/suffix "${s}". Use p. 12, § 4(a), para. 9, n. 3, or a range; separate trailing prose with a comma. Put compound locators in explanatory prose.`);
  item.label = labels[m[1]] || 'page';
  item.locator = m[2].replace(/--/g, '–');
  if (m[3] && /^(?:\d|pp?\.|§|paras?\.|n\.)/u.test(m[3])) throw Error(`@${c.citationId}: compound locator "${s}" is unsupported; put the additional pinpoint in explanatory prose.`);
  if (m[3]) item.suffix = ', ' + m[3];
  return item;
}

export function validateItems(data) {
  if (!Array.isArray(data)) throw Error('Bibliography must be a CSL-JSON array (export CSL JSON from Zotero or Juris-M).');
  const items = Object.create(null);
  const common = ['id', 'type', 'title', 'issued'];
  const required = {
    legal_case: ['jurisdiction', 'authority', 'container-title', 'volume', 'page', 'title-short'],
    legislation: ['jurisdiction', 'container-title', 'section', 'edition'],
    regulation: ['jurisdiction', 'container-title', 'section', 'edition'],
    report: ['jurisdiction', 'authority', 'number', 'genre'],
    'article-journal': ['author', 'container-title', 'volume', 'page'],
    book: ['author', 'publisher', 'edition'],
    webpage: ['author', 'URL', 'accessed'],
  };
  for (const source of data) {
    if (!Object.hasOwn(required, source.type)) throw Error(`${source.id}: unsupported source type ${source.type}; see docs/academic.md metadata matrix.`);
    for (const field of [...common, ...required[source.type]]) {
      if (!source[field] || (Array.isArray(source[field]) && !source[field].length)) throw Error(`${source.id || '(no id)'}: missing metadata ${field}; correct the reference-manager export.`);
    }
    if (typeof source.id !== 'string' || !source.id.trim()) throw Error('Citation ids must be nonempty strings.');
    if (source.author && (!Array.isArray(source.author) || source.author.some(a => !a.family && !a.literal))) throw Error(`${source.id}: author names need family or literal metadata.`);
    for (const field of ['issued', ...(source.type === 'webpage' ? ['accessed'] : [])]) {
      if (!Number.isInteger(source[field]?.['date-parts']?.[0]?.[0])) throw Error(`${source.id}: ${field} needs date-parts with a numeric year.`);
    }
    if (source.type === 'report' && source.genre !== 'bar-opinion') throw Error(`${source.id}: only reports with genre=bar-opinion are supported.`);
    if (Object.hasOwn(items, source.id)) throw Error(`Duplicate citation id: ${source.id}`);
    items[source.id] = structuredClone(source);
    if (source.type === 'report') items[source.id]['title-short'] = source.number;
    // CSL 1.0 has no regulation type. Keep original metadata in the audit output.
    if (source.type === 'regulation') items[source.id].type = 'legislation';
  }
  return items;
}

export function prepare(ast, data, style, locale, pandoc = 'pandoc') {
  const items = validateItems(data);
  const notes = [], clusters = [], warnings = [];
  function visit(n, note = null, forbidden = false, following = null) {
    if (Array.isArray(n)) {
      const next = new Array(n.length); let followingNode = null;
      for (let i = n.length - 1; i >= 0; i--) {
        next[i] = followingNode;
        if (!['Space', 'SoftBreak'].includes(n[i]?.t)) followingNode = n[i];
      }
      return n.map((x, i) => visit(x, note, forbidden, next[i]));
    }
    if (!n || typeof n !== 'object') return n;
    if (n.t === 'Note') {
      if (forbidden) throw Error('Footnotes in headings, tables, figures and captions are unsupported; move the note to a body paragraph.');
      if (note) throw Error('Nested footnotes are unsupported; split the note.');
      const info = { number: notes.length + 1, clusters: [], pure: false };
      notes.push(info);
      n.c = visit(n.c, info, forbidden);
      info.pure = n.c.length === 1 && ['Para', 'Plain'].includes(n.c[0].t)
        && n.c[0].c.length === 1 && n.c[0].c[0].t === 'Cite';
      return n;
    }
    if (n.t === 'Cite') {
      if (forbidden) throw Error('Citations in headings/captions are unsupported; move them to a body paragraph or footnote.');
      if (!note) return visit({ t: 'Note', c: [{ t: 'Para', c: [n] }] });
      const citations = n.c[0].map(citationItem);
      for (const c of citations) if (!Object.hasOwn(items, c.id)) throw Error(`Unknown citation key: ${c.id}; match the CSL-JSON id.`);
      const cluster = { index: clusters.length, note: note.number, items: citations, node: n, following };
      clusters.push(cluster); note.clusters.push(cluster);
      return n;
    }
    if (n.t === 'RawInline' || n.t === 'RawBlock') throw Error('Raw HTML/TeX is unsupported in the academic build; use native Markdown so DOCX and PDF agree.');
    // Numeric cross-references and custom note numbering are outside the contract.
    for (const k of Object.keys(n)) n[k] = visit(n[k], note, forbidden || ['Header', 'Caption', 'Image', 'Figure', 'Table'].includes(n.t));
    return n;
  }
  const metaCheck = JSON.stringify(ast.meta);
  if (metaCheck.includes('"t":"Cite"') || metaCheck.includes('"t":"Note"')) throw Error('Citations/notes in document metadata are unsupported.');
  ast.blocks = visit(ast.blocks);
  // A hidden barrier breaks ibid across explanatory/multi-authority/prose-only notes.
  const barrier = '__academic_note_barrier__';
  if (Object.hasOwn(items, barrier)) throw Error(`Reserved citation id: ${barrier}`);
  const system = { retrieveLocale: () => locale, retrieveItem: id => id === barrier
    ? { id, type: 'personal_communication', title: 'Citation context barrier' } : items[id] };
  const engine = new CSL.Engine(system, style, 'en-US');
  engine.setOutputFormat('html');
  const pre = [], rendered = [], overrides = new Map();
  function process(id, citationItems, noteIndex, index = null) {
    const [, updates] = engine.processCitationCluster({ citationID: id, citationItems, properties: { noteIndex } }, pre, []);
    pre.push([id, noteIndex]);
    if (index !== null) indexById.set(id, index);
    for (const [position, html] of updates) {
      const target = indexById.get(pre[position][0]);
      if (target !== undefined) rendered[target] = html;
    }
  }
  const indexById = new Map(), seen = new Set();
  const authorKey = item => (item.author || []).map(a => a.family || a.literal || '').join('|');
  const ambiguous = new Set(Object.values(items).filter(a => ['book', 'article-journal'].includes(a.type)
    && Object.values(items).some(b => a.id !== b.id && authorKey(a) === authorKey(b))).map(a => a.id));
  for (const note of notes) {
    const safe = note.pure && note.clusters.length === 1 && note.clusters[0].items.length === 1;
    if (!safe) process(`before-${note.number}`, [{ id: barrier }], note.number);
    for (const cluster of note.clusters) {
      process(`cite-${cluster.index}`, cluster.items, note.number, cluster.index);
      // For ambiguous note contexts and weakly supported legal types, retain full forms.
      const fullOnly = !safe || cluster.items.some(c => !['legal_case', 'article-journal', 'book'].includes(items[c.id].type)
        || (!c.locator && seen.has(c.id))
        || ambiguous.has(c.id) || c.prefix || c.suffix
        || (c.label && c.label !== 'page'));
      if (fullOnly) {
        const full = new CSL.Engine(system, style, 'en-US'); full.setOutputFormat('html');
        const [, updates] = full.processCitationCluster({ citationID: 'full', citationItems: cluster.items, properties: { noteIndex: note.number } }, [], []);
        overrides.set(cluster.index, updates[0][1]);
        warnings.push({ note: note.number, code: 'FULL_FORM', message: 'Full citation retained: complex context/affix, ambiguous author, non-page locator, or source without supported short form. Review signals, parentheticals and any desired short form.' });
      }
      for (const c of cluster.items) {
        if (seen.has(c.id)) warnings.push({ note: note.number, key: c.id, code: 'REPEAT_REVIEW', message: 'Check repeated citation: Id. context or supra first-note target, title ambiguity and pinpoints against the required Bluebook edition.' });
        seen.add(c.id);
      }
    }
    if (!safe || note.clusters.some(c => overrides.has(c.index))) process(`after-${note.number}`, [{ id: barrier }], note.number);
  }
  for (const [i, html] of overrides) rendered[i] = html;
  for (const cluster of clusters) {
    const next = cluster.following;
    if (next?.t !== 'Str' || !rendered[cluster.index].endsWith('.')) continue;
    if (/^[,;:!?\p{Ll}]/u.test(next.c)) rendered[cluster.index] = rendered[cluster.index].slice(0, -1);
    else if (next.c.startsWith('.')) next.c = next.c.slice(1);
  }
  // Parse semantic HTML once; Pandoc preserves Emph and SmallCaps in the shared AST.
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'academic-citations-'));
  let converted;
  try {
    const input = path.join(temp, 'citations.html');
    fs.writeFileSync(input, rendered.map((s, i) => `<div id="citation-${i}">${s}</div>`).join('\n'));
    converted = spawnSync(pandoc, [input, '-f', 'html', '-t', 'json'], { encoding: 'utf8', timeout: 30000 });
  } finally { fs.rmSync(temp, { recursive: true }); }
  if (converted.status !== 0) throw Error(converted.stderr || 'Pandoc HTML conversion failed');
  const parsed = JSON.parse(converted.stdout).blocks;
  if (parsed.length !== clusters.length) throw Error('Citation HTML conversion lost a cluster.');
  clusters.forEach((c, i) => {
    const block = parsed[i];
    if (block.t !== 'Div' || block.c[0][0] !== `citation-${i}` || block.c[1].length !== 1) throw Error('Unexpected citation HTML structure.');
    c.node.t = 'Span'; c.node.c = [['', ['academic-citation'], []], block.c[1][0].c];
  });
  return { ast, audit: { processor: CSL.PROCESSOR_VERSION, sourceMetadata: data, notes: notes.length,
    clusters: clusters.map(c => ({ index: c.index, note: c.note, items: c.items, html: rendered[c.index] })), warnings } };
}

if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  try {
    const [input, bib, style, locale, out, audit] = process.argv.slice(2);
    const result = prepare(JSON.parse(fs.readFileSync(input)), JSON.parse(fs.readFileSync(bib)), fs.readFileSync(style, 'utf8'), fs.readFileSync(locale, 'utf8'), process.env.PANDOC || 'pandoc');
    fs.writeFileSync(out, JSON.stringify(result.ast, null, 2));
    fs.writeFileSync(audit, JSON.stringify(result.audit, null, 2));
    for (const w of result.audit.warnings) console.error(`REVIEW note ${w.note}: ${w.code}: ${w.message}`);
  } catch (e) { console.error(`Academic citation error: ${e.message}`); process.exitCode = 1; }
}
