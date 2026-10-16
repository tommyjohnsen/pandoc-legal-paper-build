// Render the citations of a Pandoc document with citeproc-js, which understands
// CSL-M styles (version="1.1mlz1") and loads jurisdiction style modules.
// Usage: node render-cslm.mjs <pandoc-ast.json> <csl-json> <style.csl> <locale.xml> <modules-dir> <out.json>
import fs from 'node:fs';
import path from 'node:path';
import CSL from 'citeproc';

const [astFile, itemsFile, styleFile, localeFile, modulesDir, outFile] = process.argv.slice(2);
const ast = JSON.parse(fs.readFileSync(astFile, 'utf8'));
const items = Object.fromEntries(JSON.parse(fs.readFileSync(itemsFile, 'utf8')).map((i) => [i.id, i]));
const locale = fs.readFileSync(localeFile, 'utf8');

const stringify = (inl) => (inl || []).map((x) =>
  x.t === 'Str' ? x.c : x.t === 'Space' || x.t === 'SoftBreak' ? ' ' :
  Array.isArray(x.c) ? stringify(x.c.flat().filter((y) => y && y.t)) : '').join('');

const LABELS = { 'p.': 'page', 'pp.': 'page', 'sec.': 'section', 'secs.': 'section', '§': 'section', '§§': 'section', 'para.': 'paragraph', 'n.': 'note' };
function locatorOf(suffix) {
  const m = stringify(suffix).trim().replace(/^,\s*/, '').match(/^(?:(p\.|pp\.|sec\.|secs\.|§§|§|para\.|n\.)\s*)?(.*)$/);
  if (!m || !m[2]) return {};
  return { label: LABELS[m[1]] || 'page', locator: m[2].replace(/--/g, '\u2013') };
}

// Collect Cite clusters in document order.
const clusters = [];
(function walk(n) {
  if (Array.isArray(n)) return n.forEach(walk);
  if (!n || typeof n !== 'object') return;
  if (n.t === 'Cite') {
    clusters.push(n.c[0].map((c) => ({ id: c.citationId, ...locatorOf(c.citationSuffix) })));
  }
  Object.values(n).forEach(walk);
})(ast.blocks);

const sys = {
  retrieveLocale: () => locale,
  retrieveItem: (id) => { if (!items[id]) throw new Error(`unknown citation key: ${id}`); return items[id]; },
  // citeproc-js asks for jurisdiction modules (e.g. juris-us-IndigoTemp.csl) through this hook.
  retrieveStyleModule: (jurisdiction, variant) => {
    const f = path.join(modulesDir, `juris-${jurisdiction.replace(/:/g, '+')}${variant ? `-${variant}` : ''}.csl`);
    return fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : false;
  },
};

const render = (format) => {
  const engine = new CSL.Engine(sys, fs.readFileSync(styleFile, 'utf8'), 'en-US');
  engine.setOutputFormat(format);
  const out = []; const pre = [];
  clusters.forEach((cites, i) => {
    const citation = { citationID: `c${i}`, citationItems: cites, properties: { noteIndex: 0 } };
    if (i === 0) engine.updateItems(Object.keys(items));
    const [, results] = engine.processCitationCluster(citation, pre, []);
    pre.push([citation.citationID, 0]);
    for (const [idx, str] of results) out[idx] = str;
  });
  const bib = engine.bibliography && engine.makeBibliography ? engine.makeBibliography() : null;
  return { citations: out, bibliography: bib ? bib[1] : [] };
};

const html = render('html'); const text = render('text');
fs.writeFileSync(outFile, JSON.stringify({ html: html.citations, text: text.citations, bibliography_html: html.bibliography }, null, 2));
console.log(`rendered ${clusters.length} citation clusters with citeproc-js ${CSL.PROCESSOR_VERSION}`);
