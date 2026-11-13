<!-- PROVENANCE: modified-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl. -->
# Academic legal papers from Markdown

Build **native, editable DOCX footnotes and PDF footnotes from the same resolved
citation document**. Citation-only notes, explanatory Markdown notes, multiple
authorities, pinpoints, prefixes/suffixes, and conservative subsequent citations
are supported. Invalid metadata, unknown keys and unsupported citation syntax
stop the academic build with corrective diagnostics.

This is formatting automation, **not automatic Bluebook compliance or
publication readiness**. A human must review the required Bluebook edition,
every authority's support for the proposition, pinpoints and current treatment.
See the [syntax/limitations matrix](docs/academic.md) and the
[human review checklist](docs/citation-review.md).

## Capstone requirements versus choices

The supplied M.J. Capstone guide calls for 30–35 double-spaced pages, Times New
Roman, approximately 7,300–8,500 words excluding footnotes, and academic
Bluebook-style footnotes. Its approximate 100–175 footnotes is **guidance, not a
quota**. Font size and margins were not specified. The example choices of 12pt
body, 10pt notes, one-inch margins and single-spaced notes are manuscript
settings, **not UW requirements**. Confirm note spacing and other unstated
details with your program. Body/note font sizes and margins are configurable;
main-text/footnote spacing is currently fixed at double/single, respectively.

`counts.json` reports main-text words separately from footnote words;
`verification.json` reports actual PDF pages. A word count does not guarantee a
page count. Microsoft Word pagination requires opening the DOCX in your intended
Word version; this tool does not infer it from the PDF.

## Reproducible setup and demonstration

Native bootstrap targets Linux x86_64 with Python 3.12.3, pip, dpkg-deb,
fontconfig, libgraphite2, OpenSSL 3 and libstdc++ available. It installs pinned
Pandoc 3.6.4, Tectonic 0.15.0, Node 22.14.0, citeproc 2.4.63 and PyMuPDF 1.26.6
under ignored local directories, validating archive/wheel hashes. No sudo:

```bash
python3 tools/setup.py
source tools/env.sh
make test
make demo
make integration
```

First PDF use needs network access to Tectonic's versioned v33 package bundle;
its immutable bundle identity is checked. Preserve build/.cache for subsequent
offline builds of the same inputs. Setup downloads are locked in
tools/dependencies.lock.json, package-lock.json, and requirements.txt;
styles, locale and the small-cap font are vendored with verified checksums.
The [container](Dockerfile) also pins its base image digest and Debian snapshot.

Alternatively:

```bash
docker build --platform linux/amd64 -t paper-build .
mkdir -p build
docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD/build:/work/build" paper-build make test demo integration
```

The image contains the repository version copied at image build time; rebuild
the image after editing source. It includes only open demo fonts. `make demo`
explicitly uses **Liberation Serif**, so it demonstrates citations and pagination
but **does not satisfy the guide's Times New Roman requirement**. A Capstone
build requires a lawfully installed Times New Roman font, not a silent
substitution. PDF small capitals use the vendored TeX Gyre Termes companion font;
DOCX retains native smallCaps properties in the selected manuscript font.

The [committed synthetic demonstration](demonstration/README.md) includes DOCX,
PDF, citation/word/page reports and page images. All authorities are fictional.

## Build a private manuscript

Keep private sources and reference exports outside this repository, and use a
fresh output directory for every candidate. After native setup:

```bash
source tools/env.sh
python3 scripts/build_academic.py \
  --source /private/paper.md --bib /private/cited-references.json \
  --output /private/exports/candidate-001 \
  --font 'Times New Roman' --size 12 --note-size 10 --margin 1
```

All sizes/margins in that command are adjustable choices. The command refuses an
existing output directory, even after a partial build. It never rewrites Markdown,
the library export, or a previous DOCX/PDF. Outputs contain the original metadata
in citations.json; treat the entire output directory as private for a real
manuscript. Never commit Capstone drafts, licensed research, credentials or
personal reference libraries. Only fictional sample/ and deliberately curated
demonstration/ materials belong in version control.

Equivalent Make settings: `make academic ACADEMIC_SRC=... ACADEMIC_BIB=...
OUT=... FONT='Times New Roman' SIZE=12 NOTE_SIZE=10 MARGIN=1`. The default
`make` invokes the academic build, which fails if Times New Roman is absent.

## Zotero and Juris-M remain available

| Route | Use and limits |
|---|---|
| Academic + Zotero CSL JSON | New footnote workflow. Export the relevant collection; supply all required legal metadata. Plain CSL JSON often needs legal-field repair. |
| Academic + Juris-M CSL JSON | Same shared footnotes, preserving legal fields and original source type in the audit. This CSL 1.0 academic style does **not** apply CSL-M jurisdiction modules, court hierarchies or multilingual rules. |
| Legacy A: make zotero | Pandoc citeproc, locked community **bluebook-inline**; inline citations/bibliography, incomplete legal metadata rendering. **Not an equivalent substitute for academic footnotes.** CSL JSON or BibLaTeX accepted. |
| Legacy B: make jurism | citeproc-js, locked JM Indigo Book CSL-M plus US modules; inline citations/bibliography. Notes, author modes, prefixes and ambiguous suffixes now fail clearly. Not the academic manuscript path. |

In Zotero/Juris-M choose **Export Collection → CSL JSON**. Better CSL JSON can
provide stable keys. In Markdown, `[@key, p. 214]` must match the item's id.
The academic path accepts CSL JSON only, not BibLaTeX; it does not fabricate
missing court, jurisdiction, edition or statutory metadata.

Legacy commands, using fresh build directories:

```bash
make legacy legacy-test BUILD=build/legacy-001
# Individual routes: make zotero / make jurism / make compare
# Legacy inputs: SRC=paper.md A_BIB=zotero.json B_JSON=jurism.json
```

`make compare` compares the two **legacy** engines, not academic DOCX/PDF
parity. Academic parity is tested by scripts/verify_outputs.py. Legacy style
sources are locked in tools/styles.lock.json; arbitrary STYLE_A overrides
are no longer accepted as pinned builds. Style changes require a deliberate
source/checksum update and renewed tests.

## Evidence and licenses

`make test` checks syntax, short forms, failure diagnostics, metadata, word
separation, formatting choices, non-overwriting behavior and vendor hashes.
`make integration` builds the synthetic corpus in two layouts plus a note
spanning pages, inspects DOCX XML, compares PDF reference numbers and complete
footnote text, checks page dimensions/bounds, and renders all pages for human
visual inspection. Both commands are in CI. A fresh integration output can be
selected with `INTEGRATION_OUT=build/another-run make integration`.

See [test results](docs/test-results.md), [document record](docs/document-record.md)
and [third-party notices](vendor/NOTICE.md). The template is Apache-2.0;
the citation styles/derivative are CC BY-SA 3.0 and fonts keep their own licenses.
No licensed Bluebook text or real research library is included. Codex authorship
is recorded in .provenance/ledger.jsonl; no independent citation or code-review
approval is implied. Main-branch merge/release still requires the mandated
independent reviewer approvals at the exact proposed commit.
